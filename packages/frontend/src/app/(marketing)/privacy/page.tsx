import Link from 'next/link';

export default function PrivacyPage() {
    return (
        <div className="mx-auto max-w-3xl px-6 py-16">
            <h1 className="mb-2 text-3xl font-bold text-balance">개인정보처리방침</h1>
            <p className="mb-10 text-sm text-muted-foreground">최종 수정일: 2026년 1월 1일</p>

            <div className="prose prose-invert max-w-none space-y-8 text-sm leading-relaxed text-muted-foreground">
                <section>
                    <h2 className="mb-3 text-base font-semibold text-foreground">1. 개인정보 수집 항목 및 목적</h2>
                    <div className="overflow-x-auto rounded-lg border border-border">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-border bg-muted/30">
                                    <th className="px-4 py-3 text-left font-medium text-foreground">수집 항목</th>
                                    <th className="px-4 py-3 text-left font-medium text-foreground">수집 목적</th>
                                    <th className="px-4 py-3 text-left font-medium text-foreground">보유 기간</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr className="border-b border-border">
                                    <td className="px-4 py-3">이메일 주소</td>
                                    <td className="px-4 py-3">계정 식별, 서비스 알림</td>
                                    <td className="px-4 py-3">회원 탈퇴 후 30일</td>
                                </tr>
                                <tr className="border-b border-border">
                                    <td className="px-4 py-3">카카오 닉네임</td>
                                    <td className="px-4 py-3">서비스 내 프로필 표시</td>
                                    <td className="px-4 py-3">회원 탈퇴 후 30일</td>
                                </tr>
                                <tr className="border-b border-border">
                                    <td className="px-4 py-3">프로필 이미지</td>
                                    <td className="px-4 py-3">서비스 내 프로필 표시</td>
                                    <td className="px-4 py-3">회원 탈퇴 후 30일</td>
                                </tr>
                                <tr>
                                    <td className="px-4 py-3">서비스 이용 기록</td>
                                    <td className="px-4 py-3">서비스 개선, 통계 분석</td>
                                    <td className="px-4 py-3">수집일로부터 1년</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </section>

                <section>
                    <h2 className="mb-3 text-base font-semibold text-foreground">2. 개인정보 수집 방법</h2>
                    <ul className="list-disc pl-5 space-y-1">
                        <li>카카오 OAuth 로그인 시 카카오로부터 제공받는 정보</li>
                        <li>서비스 이용 과정에서 이용자가 직접 입력하는 정보</li>
                    </ul>
                </section>

                <section>
                    <h2 className="mb-3 text-base font-semibold text-foreground">3. 개인정보 제3자 제공</h2>
                    <p>
                        회사는 원칙적으로 이용자의 개인정보를 제3자에게 제공하지 않습니다.
                        다만, 다음의 경우에는 예외로 합니다.
                    </p>
                    <ul className="list-disc pl-5 space-y-1 mt-2">
                        <li>이용자가 사전에 동의한 경우</li>
                        <li>법령의 규정에 의거하거나 수사기관의 요구가 있는 경우</li>
                    </ul>
                </section>

                <section>
                    <h2 className="mb-3 text-base font-semibold text-foreground">4. 개인정보 처리 위탁</h2>
                    <div className="overflow-x-auto rounded-lg border border-border">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-border bg-muted/30">
                                    <th className="px-4 py-3 text-left font-medium text-foreground">수탁자</th>
                                    <th className="px-4 py-3 text-left font-medium text-foreground">위탁 업무</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr className="border-b border-border">
                                    <td className="px-4 py-3">Supabase</td>
                                    <td className="px-4 py-3">데이터베이스 서비스</td>
                                </tr>
                                <tr className="border-b border-border">
                                    <td className="px-4 py-3">Vercel</td>
                                    <td className="px-4 py-3">웹 서비스 호스팅</td>
                                </tr>
                                <tr>
                                    <td className="px-4 py-3">Toss Payments</td>
                                    <td className="px-4 py-3">결제 처리</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </section>

                <section>
                    <h2 className="mb-3 text-base font-semibold text-foreground">5. 개인정보 파기</h2>
                    <p>
                        회원 탈퇴 시 또는 보유 기간 만료 시 개인정보를 지체 없이 파기합니다.
                        전자적 파일 형태는 복구 불가능한 방법으로 영구 삭제하며,
                        출력물은 분쇄기로 파기합니다.
                    </p>
                </section>

                <section>
                    <h2 className="mb-3 text-base font-semibold text-foreground">6. 이용자의 권리</h2>
                    <ul className="list-disc pl-5 space-y-1">
                        <li>언제든지 자신의 개인정보를 조회, 수정, 삭제 요청할 수 있습니다.</li>
                        <li>개인정보 처리 정지를 요청할 수 있습니다.</li>
                        <li>권리 행사는 카카오톡 채널을 통해 요청해 주세요.</li>
                    </ul>
                </section>

                <section>
                    <h2 className="mb-3 text-base font-semibold text-foreground">7. 개인정보 보호책임자</h2>
                    <div className="rounded-lg border border-border bg-muted/20 p-4">
                        <ul className="space-y-1">
                            <li><span className="text-foreground/70">이름:</span> 강은구</li>
                            <li><span className="text-foreground/70">소속:</span> 하캄솔루션</li>
                            <li>
                                <span className="text-foreground/70">문의:</span>{' '}
                                <a
                                    href="https://pf.kakao.com/_GxmxcTG/chat"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-primary underline hover:text-primary/80 transition-colors"
                                >
                                    카카오톡 채널
                                </a>
                            </li>
                        </ul>
                    </div>
                </section>

                <section>
                    <h2 className="mb-3 text-base font-semibold text-foreground">8. 개인정보 침해 신고</h2>
                    <p>
                        개인정보 침해 관련 신고나 상담은 아래 기관에 문의하실 수 있습니다.
                    </p>
                    <ul className="list-disc pl-5 space-y-1 mt-2">
                        <li>개인정보 침해신고센터: privacy.kisa.or.kr (국번 없이 118)</li>
                        <li>대검찰청 사이버범죄수사단: www.spo.go.kr (02-3480-3573)</li>
                        <li>경찰청 사이버안전국: cyberbureau.police.go.kr (국번 없이 182)</li>
                    </ul>
                </section>
            </div>

            <div className="mt-12 border-t border-border/50 pt-6 flex gap-4 text-sm">
                <Link href="/terms" className="text-primary hover:text-primary/80 transition-colors">
                    이용약관 보기
                </Link>
                <Link href="/landing" className="text-muted-foreground hover:text-foreground transition-colors">
                    서비스 홈으로
                </Link>
            </div>
        </div>
    );
}
