import "./globals.css";
import Sidebar from "@/components/sidebar";
import AuthGuard from "@/components/auth-guard";
import localFont from "next/font/local";

const vazirMatn = localFont({
  src: "../../public/font/Vazirmatn-RD-Regular.woff2",
});
export const metadata={
  title:"Cafino",
  description:"Hospitality Management Platform",
  manifest:"/manifest.webmanifest",
};
export const viewport={themeColor:"#211711"};

export default function RootLayout({children}:{children:React.ReactNode}){
  return (
    <html lang="fa" dir="rtl" className={vazirMatn.className}>
      <body>
        <AuthGuard>
          <div className="flex min-h-screen w-full">
            <Sidebar />
            <main className="min-w-0 w-full flex-1 p-3 pb-6 pt-20 sm:p-6 sm:pt-20 lg:pt-6">{children}</main>
          </div>
        </AuthGuard>
      </body>
    </html>
  );
}
