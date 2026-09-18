// Brand mark. Renders a minimal shield outline with a small voice/soundwave
// notch, plus the VoxGuard wordmark. No app state, no side effects, no data
// fetching — the only behavior added is client-side navigation to the
// informational /about page when `href` is set (default). Pass href={null}
// to render the old, non-interactive mark unchanged.
import Link from "next/link";

export default function Logo({
  withWordmark = true,
  href = "/about",
}: {
  withWordmark?: boolean;
  href?: string | null;
}) {
  const mark = (
    <div className="flex items-center gap-2.5">
      <svg
        width="30"
        height="30"
        viewBox="0 0 36 36"
        fill="none"
        aria-hidden="true"
        className="shrink-0"
      >
        <path
          d="M18 3.5 30.5 8v9.2c0 8.1-5.2 14-12.5 16.3C10.7 31.2 5.5 25.3 5.5 17.2V8L18 3.5Z"
          fill="var(--accent-soft)"
          stroke="var(--accent)"
          strokeWidth="1.6"
          strokeLinejoin="round"
        />
        <path
          d="M12.5 18.4c.9 1.6 1.4 2.6 1.4 4.1M18 15.6c1.3 2.4 2 4 2 6.9M23.5 18.4c-.9 1.6-1.4 2.6-1.4 4.1"
          stroke="var(--accent)"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
      </svg>
      {withWordmark && (
        <span className="text-[15px] font-semibold tracking-tight text-foreground">
          VoxGuard
        </span>
      )}
    </div>
  );

  if (!href) return mark;

  return (
    <Link
      href={href}
      aria-label="VoxGuard — open overview page"
      className="btn-tactile rounded-control -m-1 p-1 transition-opacity hover:opacity-80 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
    >
      {mark}
    </Link>
  );
}
