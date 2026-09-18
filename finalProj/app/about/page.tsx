import type { Metadata } from "next";
import AboutClient from "./AboutClient";

export const metadata: Metadata = {
  title: "VoxGuard — Overview",
  description:
    "How VoxGuard analyzes live call audio to detect voice-cloning and impersonation risk in real time.",
};

export default function AboutPage() {
  return <AboutClient />;
}
