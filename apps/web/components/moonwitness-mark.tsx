type MoonWitnessMarkProps = { className?: string };

export function MoonWitnessMark({ className }: MoonWitnessMarkProps) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 48 48"
      fill="none"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M24 3.5 43.5 14.75v18.5L24 44.5 4.5 33.25v-18.5L24 3.5Z" stroke="currentColor" strokeWidth="1.5" />
      <path d="M31.5 10.7a15.5 15.5 0 1 0 5.8 24.4A13.7 13.7 0 0 1 31.5 10.7Z" fill="currentColor" />
      <path d="m12.5 28.5 7-7 5.2 5.2 10.8-11.2" stroke="#111214" strokeWidth="2.4" strokeLinecap="square" strokeLinejoin="miter" />
      <circle cx="35.3" cy="15.5" r="2.1" fill="#111214" />
    </svg>
  );
}
