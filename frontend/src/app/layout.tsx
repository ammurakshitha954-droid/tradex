import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Adaptive AI Trading Decision-Support System",
  description:
    "Production-grade, research-defensible, uncertainty-aware multimodal AI trading decision-support platform.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#080b10] text-[#f8fafc] min-h-screen antialiased selection:bg-blue-600/30">
        {children}
      </body>
    </html>
  );
}
