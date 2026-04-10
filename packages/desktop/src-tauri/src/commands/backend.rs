use serde::{Deserialize, Serialize};
use std::process::Command;
use tauri::Manager;

// ─── Types ────────────────────────────────────────────────────────────────────

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum BackendStatus {
    Running,
    Starting,
    Stopped,
    Error,
}

#[derive(Debug, Serialize)]
pub struct BackendStatusResponse {
    pub status: BackendStatus,
    pub message: String,
}

// ─── Internal helpers ─────────────────────────────────────────────────────────

fn generate_local_secret() -> String {
    use std::io::Read;
    let mut buf = [0u8; 32];
    if let Ok(mut f) = std::fs::File::open("/dev/urandom") {
        f.read_exact(&mut buf).ok();
    } else {
        // Windows fallback: use timestamp + pid
        let ts = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos();
        let pid = std::process::id() as u128;
        for (i, b) in buf.iter_mut().enumerate() {
            *b = ((ts >> (i % 8)) ^ (pid >> (i % 8)) ^ (i as u128)) as u8;
        }
    }
    buf.iter().map(|b| format!("{:02x}", b)).collect()
}

fn compose_file_path(app: &tauri::AppHandle) -> Result<std::path::PathBuf, String> {
    app.path()
        .resource_dir()
        .map(|dir: std::path::PathBuf| dir.join("resources").join("docker-compose.desktop.yml"))
        .map_err(|e| format!("리소스 디렉토리를 찾을 수 없습니다: {e}"))
}

fn docker_exists() -> bool {
    Command::new("docker")
        .arg("--version")
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false)
}

// ─── Commands ─────────────────────────────────────────────────────────────────

#[tauri::command]
pub fn check_docker_available() -> bool {
    docker_exists()
}

#[tauri::command]
pub fn start_local_backend(app: tauri::AppHandle) -> Result<BackendStatusResponse, String> {
    if !docker_exists() {
        return Err(
            "Docker가 설치되어 있지 않습니다. https://www.docker.com 에서 설치하세요.".into(),
        );
    }

    let compose_path = compose_file_path(&app)?;
    let secret = generate_local_secret();

    let output = Command::new("docker")
        .args(["compose", "-f"])
        .arg(&compose_path)
        .args(["up", "-d", "--pull", "missing"])
        .arg("--env")
        .arg(format!("SECRET_KEY={secret}"))
        .output()
        .map_err(|e| format!("docker compose 실행 실패: {e}"))?;

    if output.status.success() {
        Ok(BackendStatusResponse {
            status: BackendStatus::Starting,
            message: "백엔드 컨테이너를 시작하고 있습니다...".into(),
        })
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr).into_owned();
        Err(format!("컨테이너 시작 실패:\n{stderr}"))
    }
}

#[tauri::command]
pub fn stop_local_backend(app: tauri::AppHandle) -> Result<BackendStatusResponse, String> {
    if !docker_exists() {
        return Err("Docker를 찾을 수 없습니다.".into());
    }

    let compose_path = compose_file_path(&app)?;

    let output = Command::new("docker")
        .args(["compose", "-f"])
        .arg(&compose_path)
        .args(["down"])
        .output()
        .map_err(|e| format!("docker compose down 실행 실패: {e}"))?;

    if output.status.success() {
        Ok(BackendStatusResponse {
            status: BackendStatus::Stopped,
            message: "백엔드 컨테이너가 중지되었습니다.".into(),
        })
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr).into_owned();
        Err(format!("컨테이너 중지 실패:\n{stderr}"))
    }
}

#[tauri::command]
pub fn get_local_backend_status(app: tauri::AppHandle) -> BackendStatusResponse {
    if !docker_exists() {
        return BackendStatusResponse {
            status: BackendStatus::Stopped,
            message: "Docker가 설치되어 있지 않습니다.".into(),
        };
    }

    let compose_path = match compose_file_path(&app) {
        Ok(p) => p,
        Err(e) => {
            return BackendStatusResponse {
                status: BackendStatus::Error,
                message: e,
            }
        }
    };

    let output = match Command::new("docker")
        .args(["compose", "-f"])
        .arg(&compose_path)
        .args(["ps", "--format", "json"])
        .output()
    {
        Ok(o) => o,
        Err(e) => {
            return BackendStatusResponse {
                status: BackendStatus::Error,
                message: format!("상태 확인 실패: {e}"),
            }
        }
    };

    if !output.status.success() {
        return BackendStatusResponse {
            status: BackendStatus::Stopped,
            message: "컨테이너가 실행 중이지 않습니다.".into(),
        };
    }

    let stdout = String::from_utf8_lossy(&output.stdout);

    if stdout.trim().is_empty() {
        return BackendStatusResponse {
            status: BackendStatus::Stopped,
            message: "컨테이너가 없습니다.".into(),
        };
    }

    let first_line = stdout.lines().next().unwrap_or("").trim();

    #[derive(Deserialize)]
    struct ContainerInfo {
        #[serde(rename = "State")]
        state: Option<String>,
        #[serde(rename = "Health")]
        health: Option<String>,
    }

    match serde_json::from_str::<ContainerInfo>(first_line) {
        Ok(info) => {
            let state = info.state.as_deref().unwrap_or("unknown");
            let health = info.health.as_deref().unwrap_or("");

            match (state, health) {
                ("running", "healthy") => BackendStatusResponse {
                    status: BackendStatus::Running,
                    message: "백엔드가 정상 실행 중입니다.".into(),
                },
                ("running", "starting") | ("running", "") => BackendStatusResponse {
                    status: BackendStatus::Starting,
                    message: "백엔드를 시작하고 있습니다...".into(),
                },
                ("running", h) => BackendStatusResponse {
                    status: BackendStatus::Starting,
                    message: format!("컨테이너 상태: {h}"),
                },
                (s, _) => BackendStatusResponse {
                    status: BackendStatus::Stopped,
                    message: format!("컨테이너 상태: {s}"),
                },
            }
        }
        Err(_) => BackendStatusResponse {
            status: BackendStatus::Error,
            message: "상태 파싱 실패".into(),
        },
    }
}
