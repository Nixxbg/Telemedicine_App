import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Telemedicine App",
  description: "Secure telemedicine platform for patient-doctor consultations",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
