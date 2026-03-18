import type { Metadata } from "next";
import { Fraunces, Inter } from "next/font/google";
import "@/app/globals.css";

const display = Fraunces({ subsets: ["latin"], weight: ["600", "700"], variable: "--font-display" });
const body = Inter({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--font-body" });

export const metadata: Metadata = {
  title: "Meal Prep Studio",
  description: "Turn messy goals into a ready-to-cook weekly meal prep artifact."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${display.variable} ${body.variable}`}>{children}</body>
    </html>
  );
}
