import "./globals.css";
import "./mobile.css";
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
          <div className="flex min-h-screen min-w-0">
            <Sidebar />
            <main className="w-full min-w-0 flex-1 overflow-x-hidden p-3 pt-[4.5rem] sm:p-5 sm:pt-[4.75rem] lg:p-6">{children}</main>
          </div>
        </AuthGuard>
      </body>
    </html>
  );
}
