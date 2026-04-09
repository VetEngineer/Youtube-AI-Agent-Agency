import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Youtube,
  Activity,
  Settings,
  Rocket,
  Search,
  FileText,
  Mic,
  Film,
  Upload,
  ChevronRight,
  Info,
  Key,
  CreditCard,
} from "lucide-react";

const pipelineSteps = [
  {
    step: 1,
    icon: Search,
    title: "브랜드 리서치",
    description: "입력한 주제와 채널 정보를 바탕으로 타겟 시청자와 콘텐츠 방향을 분석합니다.",
  },
  {
    step: 2,
    icon: FileText,
    title: "원고 생성",
    description: "Claude AI가 SEO를 고려한 영상 원고를 작성합니다.",
  },
  {
    step: 3,
    icon: Search,
    title: "SEO 최적화",
    description: "GPT-4o가 제목, 설명, 태그를 최적화하여 검색 노출을 높입니다.",
  },
  {
    step: 4,
    icon: Mic,
    title: "미디어 생성",
    description: "ElevenLabs TTS로 음성을 생성하고 썸네일 이미지를 만듭니다.",
  },
  {
    step: 5,
    icon: Film,
    title: "영상 편집",
    description: "FFmpeg으로 음성, 이미지, 자막을 합성하여 최종 영상을 제작합니다.",
  },
  {
    step: 6,
    icon: Upload,
    title: "YouTube 업로드",
    description: "완성된 영상을 YouTube Studio에 자동으로 업로드합니다.",
  },
];

const quickStartSteps = [
  {
    number: "01",
    title: "채널 등록",
    description: "Channels 메뉴에서 YouTube 채널을 등록합니다. 채널 ID는 영문/숫자/하이픈만 사용 가능합니다.",
    href: "/channels",
    linkText: "채널 등록하기",
  },
  {
    number: "02",
    title: "API 키 설정",
    description: "Settings → API Keys에서 API 키를 생성하고 저장해 두세요. 파이프라인 실행 시 필요합니다.",
    href: "/settings",
    linkText: "설정 열기",
  },
  {
    number: "03",
    title: "파이프라인 실행",
    description: "Dashboard의 'Create Pipeline' 버튼을 클릭하고 영상 주제를 입력합니다. Dry Run으로 먼저 테스트해 보세요.",
    href: "/pipelines/new",
    linkText: "파이프라인 만들기",
  },
];

const faqItems = [
  {
    q: "Dry Run이란 무엇인가요?",
    a: "실제 AI 모델을 호출하지 않고 파이프라인 각 단계를 시뮬레이션합니다. 비용 없이 설정이 올바른지 확인할 수 있습니다.",
  },
  {
    q: "Brand Name은 왜 입력하나요?",
    a: "원고와 콘텐츠에 브랜드 정체성을 반영합니다. 예: 'TechReview'를 입력하면 해당 브랜드 스타일로 스크립트가 작성됩니다.",
  },
  {
    q: "채널 한도를 초과하면 어떻게 되나요?",
    a: "Free 플랜은 채널 1개, Pro는 5개까지 등록 가능합니다. 한도 초과 시 채널 추가가 차단되며 요금제 업그레이드가 필요합니다.",
  },
  {
    q: "파이프라인 실행 한도는?",
    a: "Free 플랜은 월 5회, Pro는 50회, Enterprise는 무제한 실행 가능합니다. 사용량은 Dashboard에서 확인할 수 있습니다.",
  },
  {
    q: "파이프라인이 실패했을 때 어떻게 하나요?",
    a: "Pipelines 목록에서 해당 실행을 클릭하면 단계별 로그를 확인할 수 있습니다. API 키나 채널 설정 오류가 주요 원인입니다.",
  },
];

export default function GuidePage() {
  return (
    <div className="max-w-4xl mx-auto space-y-10 pb-12">
      {/* Header */}
      <div className="space-y-2">
        <h2 className="text-3xl font-bold text-balance">사용 가이드</h2>
        <p className="text-muted-foreground text-lg text-pretty">
          YouTube AI Agent Agency를 처음 사용하는 분을 위한 빠른 시작 안내서입니다.
        </p>
      </div>

      {/* Quick Start */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <Rocket className="h-5 w-5 text-primary" />
          <h3 className="text-xl font-semibold">빠른 시작 (3단계)</h3>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {quickStartSteps.map((step) => (
            <Card key={step.number} className="relative overflow-hidden">
              <div className="absolute top-3 right-3 text-5xl font-black text-muted/20 select-none">
                {step.number}
              </div>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">{step.title}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-muted-foreground">{step.description}</p>
                <Button variant="outline" size="sm" asChild className="w-full">
                  <Link href={step.href}>
                    {step.linkText} <ChevronRight className="ml-1 h-3 w-3" />
                  </Link>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Pipeline Steps */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary" />
          <h3 className="text-xl font-semibold">파이프라인 6단계</h3>
        </div>
        <p className="text-sm text-muted-foreground">
          주제를 입력하면 AI가 아래 6단계를 자동으로 실행하여 YouTube 영상을 생성합니다.
        </p>
        <div className="grid gap-3 md:grid-cols-2">
          {pipelineSteps.map((s) => (
            <div
              key={s.step}
              className="flex items-start gap-4 p-4 rounded-lg border bg-card"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary font-semibold text-sm">
                {s.step}
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <s.icon className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium text-sm">{s.title}</span>
                </div>
                <p className="text-xs text-muted-foreground">{s.description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Menu Guide */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <Info className="h-5 w-5 text-primary" />
          <h3 className="text-xl font-semibold">메뉴 설명</h3>
        </div>
        <div className="space-y-3">
          {[
            {
              icon: Activity,
              name: "Pipelines",
              desc: "AI 콘텐츠 생성 작업 목록입니다. 각 파이프라인은 하나의 영상을 만드는 6단계 프로세스입니다. 실행 중인 작업의 진행 상황과 로그를 확인할 수 있습니다.",
            },
            {
              icon: Youtube,
              name: "Channels",
              desc: "파이프라인이 영상을 업로드할 YouTube 채널을 등록합니다. 채널별로 브랜드 가이드를 설정하면 일관된 스타일로 콘텐츠가 생성됩니다.",
            },
            {
              icon: Settings,
              name: "Settings",
              desc: "API 키 관리, 요금제 확인 및 업그레이드, 계정 설정을 변경합니다. API 키는 외부 서비스 접근에 사용되며 안전하게 보관하세요.",
            },
          ].map((item) => (
            <div key={item.name} className="flex gap-4 p-4 rounded-lg border bg-card">
              <item.icon className="h-5 w-5 text-muted-foreground mt-0.5 shrink-0" />
              <div>
                <span className="font-medium">{item.name}</span>
                <p className="text-sm text-muted-foreground mt-1">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Billing */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <CreditCard className="h-5 w-5 text-primary" />
          <h3 className="text-xl font-semibold">요금제</h3>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {[
            {
              name: "Free",
              color: "secondary",
              limits: ["파이프라인 월 5회", "채널 1개", "기본 기능"],
            },
            {
              name: "Pro",
              color: "default",
              limits: ["파이프라인 월 50회", "채널 5개", "우선 처리"],
            },
            {
              name: "Enterprise",
              color: "outline",
              limits: ["파이프라인 무제한", "채널 무제한", "전용 지원"],
            },
          ].map((plan) => (
            <Card key={plan.name}>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Badge variant={plan.color as "secondary" | "default" | "outline"}>
                    {plan.name}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1">
                  {plan.limits.map((l) => (
                    <li key={l} className="text-sm text-muted-foreground flex items-center gap-2">
                      <span className="h-1 w-1 rounded-full bg-muted-foreground shrink-0" />
                      {l}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>
        <p className="text-xs text-muted-foreground">
          요금제는 Settings → Plans에서 변경할 수 있습니다. 한국은 Toss Payments, 해외는 Stripe로 결제됩니다.
        </p>
      </section>

      {/* FAQ */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <Key className="h-5 w-5 text-primary" />
          <h3 className="text-xl font-semibold">자주 묻는 질문</h3>
        </div>
        <div className="space-y-3">
          {faqItems.map((item) => (
            <div key={item.q} className="rounded-lg border p-4 space-y-2">
              <p className="font-medium text-sm">{item.q}</p>
              <p className="text-sm text-muted-foreground">{item.a}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <div className="rounded-xl bg-primary/5 border border-primary/20 p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <p className="font-semibold">준비됐나요?</p>
          <p className="text-sm text-muted-foreground">온보딩 마법사로 첫 채널과 파이프라인을 설정해 보세요.</p>
        </div>
        <Button asChild>
          <Link href="/onboarding">
            <Rocket className="mr-2 h-4 w-4" />
            온보딩 시작하기
          </Link>
        </Button>
      </div>
    </div>
  );
}
