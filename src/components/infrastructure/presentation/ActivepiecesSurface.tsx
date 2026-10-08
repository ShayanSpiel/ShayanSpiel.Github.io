import { usePresentationLocale } from './Localization';
import { SurfaceIcon } from './ComponentSurface';

/** Schematic reconstruction of the public Activepieces builder, not a connected editor.
 * Reference: https://www.activepieces.com/blog/how-to-build-ai-sales-agents-for-cold-email-outreach
 * The public editor's vertical steps, add-step junctions and configuration sidebar are retained.
 */
export default function ActivepiecesSurface({ showBuild = false }: { showBuild?: boolean }) {
  const locale = usePresentationLocale();
  const t = (en: string, fa: string) => locale === 'fa' ? fa : en;
  const steps = [
    ['message-square', t('New support ticket', 'تیکت جدید پشتیبانی'), 'Webhook'],
    ['link', t('Get order + policy', 'دریافت سفارش و سیاست'), 'HTTP'],
    ['brain', t('Draft grounded reply', 'پیش‌نویس پاسخ مستند'), 'AI'],
    ['network-chart', t('Evidence available?', 'شواهد کافی است؟'), 'Router'],
  ];
  return <div className={`ap-editor-example${showBuild ? ' ap-editor-example--build' : ''}`} dir="ltr">
    {showBuild && <div className="ap-mcp-handoff"><div><img src="/assets/infrastructure/logos/thesvg/codex.svg" alt=""/><strong>Codex</strong><span>→ MCP</span></div><code>ap_build_flow</code><span className="ap-handoff-arrow">→</span><b>{t('Draft workflow', 'گردش‌کار پیش‌نویس')}</b><small>{t('Illustrative call', 'فراخوانی نمایشی')}</small></div>}
    <div className="ap-app-shell">
      <header className="ap-editor-toolbar"><span className="ap-home">‹</span><img src="/assets/infrastructure/logos/activepieces.svg" alt="Activepieces"/><strong>{t('Delivery exception', 'استثنای تحویل')}</strong><span className="ap-draft-badge">{t('Draft', 'پیش‌نویس')}</span><span className="ap-editor-more">···</span><span className="ap-test-button">▷ {t('Test Flow', 'آزمون گردش‌کار')}</span><span className="ap-publish-button">{t('Publish', 'انتشار')}</span></header>
      <div className="ap-editor-content">
        <div className="ap-flow-canvas">
          <svg className="ap-flow-wires" viewBox="0 0 940 486" aria-hidden="true"><path d="M470 86V110 M470 172V196 M470 258V282 M470 344V374 M470 374H260V416 M470 374H680V416"/><path className="ap-wire-arrow" d="m466 106 4 4 4-4m-8 82 4 4 4-4m-8 82 4 4 4-4m-218 130 4 4 4-4m412-4 4 4 4-4"/></svg>
          {steps.map(([icon,title,piece],i)=><div className={`ap-editor-node ap-editor-node--${i}${i===3?' ap-editor-node--selected':''}`} key={piece} style={{top:24+i*86}}><span className={`ap-piece-icon ap-piece-icon--${piece.toLowerCase()}`}><SurfaceIcon name={icon}/></span><div><strong>{i+1}. {title}</strong><small>{piece}</small></div><span className="ap-node-chevron">⌄</span></div>)}
          {[0,1,2].map(i=><span className="ap-add-step" style={{top:90+i*86}} key={i}>+</span>)}
          <span className="ap-branch-label ap-branch-label--yes">{t('Has evidence', 'با شواهد')}</span><span className="ap-branch-label ap-branch-label--no">{t('Otherwise', 'در غیر این صورت')}</span>
          <div className="ap-editor-node ap-editor-node--branch ap-editor-node--reply"><span className="ap-piece-icon ap-piece-icon--reply"><SurfaceIcon name="check-circle"/></span><div><strong>{t('Prepare reply', 'آماده‌سازی پاسخ')}</strong><small>{t('For approval', 'برای تأیید')}</small></div></div>
          <div className="ap-editor-node ap-editor-node--branch ap-editor-node--review"><span className="ap-piece-icon ap-piece-icon--review"><SurfaceIcon name="group"/></span><div><strong>{t('Human review', 'بازبینی انسانی')}</strong><small>{t('Hold sending', 'توقف ارسال')}</small></div></div>
          <div className="ap-canvas-controls"><span>↖</span><span>−</span><span>100%</span><span>+</span><span>⛶</span></div>
        </div>
        <aside className="ap-config-pane" dir={locale==='fa'?'rtl':'ltr'}><header><strong>{t('Router', 'مسیریاب')}</strong><span>×</span></header><div className="ap-config-tabs"><b>{t('Settings', 'تنظیمات')}</b><span>{t('Test', 'آزمون')}</span></div><label>{t('Condition', 'شرط')}<span className="ap-config-input"><code>order_found</code><b>⌄</b></span></label><div className="ap-condition-op">{t('is equal to', 'برابر است با')}</div><span className="ap-config-input"><code>true</code><b>⌄</b></span><label>{t('And · must also be true', 'و · باید برقرار باشد')}<span className="ap-config-input"><code>evidence_current</code><b>⌄</b></span></label><div className="ap-config-help"><SurfaceIcon name="shield"/><p>{t('Missing order or stale evidence goes to human review.','سفارش نامشخص یا شواهد قدیمی به بازبینی انسانی ارجاع می‌شود.')}</p></div><footer><span className="ap-config-test">{t('Test Step', 'آزمون مرحله')}</span><small>{t('No test result shown', 'نتیجهٔ آزمون نمایش داده نشده')}</small></footer></aside>
      </div>
      <footer className="ap-editor-caption">{t('Illustrative Activepieces editor · draft only · not published', 'بازسازی نمایشی ویرایشگر Activepieces · فقط پیش‌نویس · منتشر نشده')}</footer>
    </div>
    {!showBuild && <div className="ap-editor-next"><SurfaceIcon name="shield"/><span>{t('Next: validate the flow, run acceptance cases, inspect failures, repair.','گام بعدی: اعتبارسنجی، اجرای نمونه‌های پذیرش، بررسی شکست‌ها و اصلاح.')}</span></div>}
  </div>;
}
