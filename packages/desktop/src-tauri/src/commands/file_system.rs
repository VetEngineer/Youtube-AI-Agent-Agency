// M4: 파일시스템 헬퍼 — 출력 디렉토리 존재 여부 검증
// 프론트에서 dialog.open()으로 경로를 선택한 후 이 커맨드로 검증한다.

#[tauri::command]
pub fn validate_output_dir(path: String) -> Result<(), String> {
    let p = std::path::Path::new(&path);
    if !p.exists() {
        return Err(format!("디렉토리가 존재하지 않습니다: {path}"));
    }
    if !p.is_dir() {
        return Err(format!("디렉토리가 아닙니다: {path}"));
    }
    Ok(())
}
