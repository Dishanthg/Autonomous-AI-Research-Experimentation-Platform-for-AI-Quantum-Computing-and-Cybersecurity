import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement> & { size?: number };

function base(props: IconProps) {
  const { size = 16, ...rest } = props;
  return {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.75,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    ...rest,
  };
}

export const IconGrid = (p: IconProps) => (
  <svg {...base(p)}><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></svg>
);

export const IconAtom = (p: IconProps) => (
  <svg {...base(p)}>
    <circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none" />
    <ellipse cx="12" cy="12" rx="9" ry="3.6" />
    <ellipse cx="12" cy="12" rx="9" ry="3.6" transform="rotate(60 12 12)" />
    <ellipse cx="12" cy="12" rx="9" ry="3.6" transform="rotate(120 12 12)" />
  </svg>
);

export const IconShield = (p: IconProps) => (
  <svg {...base(p)}><path d="M12 3l7 3v6c0 4.5-3 7.7-7 9-4-1.3-7-4.5-7-9V6l7-3z" /><path d="M9 12l2 2 4-4.5" /></svg>
);

export const IconFlask = (p: IconProps) => (
  <svg {...base(p)}><path d="M9 3h6" /><path d="M10 3v6.5L4.8 18a1.8 1.8 0 0 0 1.55 2.7h11.3A1.8 1.8 0 0 0 19.2 18L14 9.5V3" /><path d="M8 15h8" /></svg>
);

export const IconLock = (p: IconProps) => (
  <svg {...base(p)}><rect x="4.5" y="10.5" width="15" height="10" rx="2" /><path d="M8 10.5V7a4 4 0 0 1 8 0v3.5" /></svg>
);

export const IconActivity = (p: IconProps) => (
  <svg {...base(p)}><path d="M3 12h4l2.5 8L13.5 4 16 12h5" /></svg>
);

export const IconClipboard = (p: IconProps) => (
  <svg {...base(p)}><rect x="6" y="4" width="12" height="17" rx="2" /><rect x="9" y="2.3" width="6" height="3.2" rx="1" /><path d="M9 11h6M9 15h6" /></svg>
);

export const IconGitBranch = (p: IconProps) => (
  <svg {...base(p)}><circle cx="6" cy="5" r="2" /><circle cx="6" cy="19" r="2" /><circle cx="18" cy="9" r="2" /><path d="M6 7v10" /><path d="M6 15c0-4.5 3-6 8-6h2" /><path d="M17 7v0" /></svg>
);

export const IconSearch = (p: IconProps) => (
  <svg {...base(p)}><circle cx="10.5" cy="10.5" r="6.5" /><path d="M20 20l-4.3-4.3" /></svg>
);

export const IconDatabase = (p: IconProps) => (
  <svg {...base(p)}><ellipse cx="12" cy="5.5" rx="7.5" ry="2.8" /><path d="M4.5 5.5V18c0 1.5 3.4 2.8 7.5 2.8s7.5-1.3 7.5-2.8V5.5" /><path d="M4.5 12c0 1.5 3.4 2.8 7.5 2.8s7.5-1.3 7.5-2.8" /></svg>
);

export const IconTarget = (p: IconProps) => (
  <svg {...base(p)}><circle cx="12" cy="12" r="8.5" /><circle cx="12" cy="12" r="4.8" /><circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" /></svg>
);

export const IconLogOut = (p: IconProps) => (
  <svg {...base(p)}><path d="M14 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-2" /><path d="M9 12h11m0 0-3-3m3 3-3 3" /></svg>
);

export const IconPlus = (p: IconProps) => (
  <svg {...base(p)}><path d="M12 5v14M5 12h14" /></svg>
);

export const IconCheck = (p: IconProps) => (
  <svg {...base(p)}><path d="M4 12.5l5 5L20 6" /></svg>
);

export const IconAlertTriangle = (p: IconProps) => (
  <svg {...base(p)}><path d="M12 3.5 2.5 20h19L12 3.5z" /><path d="M12 10v4" /><circle cx="12" cy="17" r="0.6" fill="currentColor" stroke="none" /></svg>
);

export const IconAlertCircle = (p: IconProps) => (
  <svg {...base(p)}><circle cx="12" cy="12" r="9" /><path d="M12 8v5" /><circle cx="12" cy="16" r="0.6" fill="currentColor" stroke="none" /></svg>
);

export const IconClock = (p: IconProps) => (
  <svg {...base(p)}><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3.5 2" /></svg>
);

export const IconChevronRight = (p: IconProps) => (
  <svg {...base(p)}><path d="M9 5l7 7-7 7" /></svg>
);

export const IconArrowRight = (p: IconProps) => (
  <svg {...base(p)}><path d="M4 12h16M13 5l7 7-7 7" /></svg>
);

export const IconFileText = (p: IconProps) => (
  <svg {...base(p)}><path d="M7 2.5h7l4 4V20a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 6 20V4a1.5 1.5 0 0 1 1-1.5z" /><path d="M14 2.5V7h4" /><path d="M9 12h6M9 15.5h6M9 8.5h2" /></svg>
);

export const IconInbox = (p: IconProps) => (
  <svg {...base(p)}><path d="M3.5 12h5l1.5 3h4l1.5-3h5" /><path d="M5.5 4h13l2 8v6a1.5 1.5 0 0 1-1.5 1.5H5A1.5 1.5 0 0 1 3.5 18v-6l2-8z" /></svg>
);

export const IconX = (p: IconProps) => (
  <svg {...base(p)}><path d="M6 6l12 12M18 6L6 18" /></svg>
);

export const IconCpu = (p: IconProps) => (
  <svg {...base(p)}><rect x="7" y="7" width="10" height="10" rx="1.5" /><rect x="10" y="2.5" width="4" height="3" /><rect x="10" y="18.5" width="4" height="3" /><rect x="2.5" y="10" width="3" height="4" /><rect x="18.5" y="10" width="3" height="4" /></svg>
);

export const IconInfo = (p: IconProps) => (
  <svg {...base(p)}><circle cx="12" cy="12" r="9" /><path d="M12 11v6" /><circle cx="12" cy="7.7" r="0.6" fill="currentColor" stroke="none" /></svg>
);
