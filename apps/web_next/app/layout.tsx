import type { Metadata } from "next";
import type { ReactNode } from "react";

import { SessionProvider } from "../components/session-provider";
import "./globals.css";

export const metadata: Metadata = {
  title: "DevForge Web Auth Pilot",
  description: "Real-browser proof for DevForge web authentication/session foundations.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
