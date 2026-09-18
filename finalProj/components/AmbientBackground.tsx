// Purely decorative. Fixed, behind everything, non-interactive — adds
// visual depth without affecting layout, scroll size, or any app logic.
export default function AmbientBackground() {
  return <div aria-hidden="true" className="ambient-backdrop" />;
}
