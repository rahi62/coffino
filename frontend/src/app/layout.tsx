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
          <div className="flex min-h-screen w-full min-w-0">
            <Sidebar />
            <main className="min-w-0 w-full flex-1 p-3 pb-[calc(5.5rem+env(safe-area-inset-bottom,0px))] pt-[4.5rem] md:p-5 xl:p-6 md:pb-5">{children}</main>
          </div>
        </AuthGuard>
      </body>
    </html>
  );
}
