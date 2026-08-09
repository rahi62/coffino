import "./globals.css";
import Sidebar from "@/components/sidebar";
import AuthGuard from "@/components/auth-guard";

export const metadata={
  title:"Cafino",
  description:"Hospitality Management Platform",
  manifest:"/manifest.webmanifest",
};
export const viewport={themeColor:"#211711"};

export default function RootLayout({children}:{children:React.ReactNode}){
  return <html lang="fa" dir="rtl"><body>
    <AuthGuard>
      <div className="flex flex-row-reverse min-h-screen">
        <Sidebar/>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </AuthGuard>
  </body></html>;
}
