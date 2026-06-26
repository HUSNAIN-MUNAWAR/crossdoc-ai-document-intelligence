import "./globals.css";

export const metadata = {
  title: "CrossDoc AI | Document Intelligence",
  description: "Multi-document OCR, structured extraction, reconciliation, and explainable risk intelligence.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
