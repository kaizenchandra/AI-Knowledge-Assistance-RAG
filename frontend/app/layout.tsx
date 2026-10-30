import type { Metadata } from "next";
import "./style.css";
export const metadata: Metadata = {
  title: "Knowledge Intelligence",
  description: "Evidence you can work with",
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
