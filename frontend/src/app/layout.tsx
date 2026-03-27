import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Providers } from "@/components/layout/providers";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin", "latin-ext"],
});

export const metadata: Metadata = {
  title: "HM Digital — Upravljanje pacijentima poliklinike | CEZIH integracija",
  description:
    "Cloud sustav za upravljanje pacijentima hrvatskih poliklinika s integracijom CEZIH (e-Nalaz, e-Uputnica, e-Recept, eNaručivanje). Registracija, termini, medicinski kartoni i kompatibilnost sa Zakonom o podacima i informacijama u zdravstvu.",
  keywords: [
    "CEZIH",
    "e-Nalaz",
    "e-Uputnica",
    "e-Recept",
    "poliklinika",
    "ordinacija",
    "upravljanje pacijentima",
    "medicinski karton",
    "HZZO",
    "Hrvatska",
  ],
  openGraph: {
    title: "HM Digital — Upravljanje pacijentima poliklinike",
    description:
      "Cloud sustav za poliklinike s CEZIH integracijom. Moderni interfejs, sigurnost, GDPR usklađenost.",
    type: "website",
    locale: "hr_HR",
    siteName: "HM Digital Medical MVP",
  },
  twitter: {
    card: "summary_large_image",
    title: "HM Digital — Upravljanje pacijentima poliklinike",
    description:
      "Cloud sustav za poliklinike s CEZIH integracijom. Moderni interfejs, sigurnost, GDPR usklađenost.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="hr" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
