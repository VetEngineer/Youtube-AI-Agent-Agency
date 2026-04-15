import Link from 'next/link';

export default function TermsPage() {
    return (
        <div className="mx-auto max-w-3xl px-6 py-16">
            <h1 className="mb-2 text-3xl font-bold text-balance">이용약관</h1>
            <p className="mb-10 text-sm text-muted-foreground">최종 수정일: 2026년 1월 1일</p>

            <div className="prose prose-invert max-w-none space-y-8 text-sm leading-relaxed text-muted-foreground">
                <section>
                    <h2 className="mb-3 text-base font-semibold text-foreground">제1조 (목적)</h2>
                    <p>
                        본 약관은 하캄솔루션(이하 "회사")이 운영하는 YouTube AI Agent Agency(이하 "서비스")의 이용에 관한 조건 및 절차,
                        회사와 이용자 간의 권리·의무 및 책임 사항을 규정함을 목적으로 합니다.
                    </p>
                </section>

                <section>
                    <h2 className="mb-3 text-base font-semibold text-foreground">제2조 (서비스 내용)</h2>
                    <p>
                        서비스는 AI 에이전트 기반 YouTube 콘텐츠 자동 생성 파이프라인을 제공합니다.
                        주요 기능으로는 브랜드 리서치, 원고 생성, SEO 최적화, 미디어 생성, 영상 편집, YouTube 업로드 자동화가 포함됩니다.
                    </p>
                </section>

                <section>
                    <h2 className="mb-3 text-base font-semibold text-foreground">제3조 (이용 자격)</h2>
                    <ul className="list-disc pl-5 space-y-1">
                        <li>만 14세 이상의 개인 또는 법인이 이용할 수 있습니다.</li>
                        <li>카카오 계정을 통해 본인 인증 후 이용 가능합니다.</li>
                        <li>타인의 정보를 도용하거나 허위 정보를 제공한 경우 이용이 제한될 수 있습니다.</li>
                    </ul>
                </section>

                <section>
                    <h2 className="mb-3 text-base font-semibold text-foreground">제4조 (요금제 및 결제)</h2>
                    <p>
                        서비스는 Free, Pro(월 ₩29,000), Enterprise(월 ₩99,000) 플랜을 제공합니다.
                        유료 플랜은 Toss Payments를 통해 결제하며, 매월 자동 갱신됩니다.
                        구독 취소는 다음 결제일 1일 전까지 가능하며, 이미 결제된 금액은 환불되지 않습니다.
                    </p>
                </section>

                <section>
                    <h2 className="mb-3 text-base font-semibold text-foreground">제5조 (이용자 의무)</h2>
                    <ul className="list-disc pl-5 space-y-1">
                        <li>저작권법을 포함한 관련 법령을 준수해야 합니다.</li>
                        <li>서비스를 이용하여 생성된 콘텐츠의 적법성은 이용자 본인이 책임집니다.</li>
                        <li>서비스의 악의적 이용, 자동화된 대량 요청, 해킹 시도는 금지됩니다.</li>
                        <li>타인의 저작권·초상권·명예를 침해하는 콘텐츠 생성은 금지됩니다.</li>
                    </ul>
                </section>

                <section>
                    <h2 className="mb-3 text-base font-semibold text-foreground">제6조 (지식재산권)</h2>
                    <p>
                        서비스 자체(코드, UI, 알고리즘 등)의 지식재산권은 회사에 귀속됩니다.
                        이용자가 서비스를 통해 생성한 콘텐츠(원고, 영상 등)의 저작권은 이용자에게 귀속됩니다.
                    </p>
                </section>

                <section>
                    <h2 className="mb-3 text-base font-semibold text-foreground">제7조 (서비스 제한 및 중단)</h2>
                    <p>
                        회사는 시스템 점검, 천재지변, API 제공사의 정책 변경 등 불가피한 사유가 있는 경우 서비스 제공을 일시 중단할 수 있습니다.
                        서비스 중단 시 사전 공지를 원칙으로 하나, 긴급한 경우 사후 공지할 수 있습니다.
                    </p>
                </section>

                <section>
                    <h2 className="mb-3 text-base font-semibold text-foreground">제8조 (면책 조항)</h2>
                    <p>
                        회사는 AI가 생성한 콘텐츠의 정확성, 완전성, 적합성을 보증하지 않습니다.
                        생성된 콘텐츠로 인한 YouTube 계정 제재, 저작권 분쟁 등에 대해 회사는 책임을 지지 않습니다.
                    </p>
                </section>

                <section>
                    <h2 className="mb-3 text-base font-semibold text-foreground">제9조 (분쟁 해결)</h2>
                    <p>
                        본 약관과 관련된 분쟁은 대한민국 법률에 따르며, 대전지방법원을 관할 법원으로 합니다.
                    </p>
                </section>

                <section>
                    <h2 className="mb-3 text-base font-semibold text-foreground">제10조 (문의)</h2>
                    <p>
                        이용약관에 관한 문의는{' '}
                        <a
                            href="https://pf.kakao.com/_GxmxcTG/chat"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary underline hover:text-primary/80 transition-colors"
                        >
                            카카오톡 채널
                        </a>
                        을 통해 접수해 주세요.
                    </p>
                    <p className="mt-2">
                        사업자: 하캄솔루션 | 대표: 강은구 | 사업자등록번호: 435-17-01222
                    </p>
                </section>
            </div>

            <div className="mt-12 border-t border-border/50 pt-6 flex gap-4 text-sm">
                <Link href="/privacy" className="text-primary hover:text-primary/80 transition-colors">
                    개인정보처리방침 보기
                </Link>
                <Link href="/landing" className="text-muted-foreground hover:text-foreground transition-colors">
                    서비스 홈으로
                </Link>
            </div>
        </div>
    );
}
