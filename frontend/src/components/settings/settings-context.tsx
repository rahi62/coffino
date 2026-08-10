"use client";
import {createContext,useContext,useEffect,useMemo,useState} from "react";
import {api} from "@/lib/api";

export type SettingsBusiness={id:number;name:string;business_type:string;deployment_type:string;is_active:boolean};
export type SettingsBranch={id:number;business:number;name:string;address:string;phone:string;is_active:boolean};
export type SettingsModule={id:number;business:number;key:string;enabled:boolean;config:Record<string,unknown>};
export type SettingsContextData={
  business:SettingsBusiness;
  branches:SettingsBranch[];
  modules:SettingsModule[];
  permissions:Record<string,boolean>;
  current_branch:number|null;
  role:string;
};

type Value={data:SettingsContextData|null;loading:boolean;error:string;selectedBranchId:number|null;selectedBranch:SettingsBranch|null;setSelectedBranchId:(id:number)=>void;refresh:()=>Promise<void>;can:(code:string)=>boolean};
const Ctx=createContext<Value|null>(null);
const storageKey="cafino_settings_branch";

export function SettingsProvider({children}:{children:React.ReactNode}){
  const [data,setData]=useState<SettingsContextData|null>(null);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState("");
  const [selectedBranchId,setSelectedBranchState]=useState<number|null>(null);

  const refresh=async()=>{
    setLoading(true);setError("");
    try{
      const x=await api<SettingsContextData>("/settings/context/");
      setData(x);
      const stored=typeof window!=="undefined"?Number(localStorage.getItem(storageKey)||0):0;
      const candidate=x.branches.some(b=>b.id===stored)?stored:(x.current_branch&&x.branches.some(b=>b.id===x.current_branch)?x.current_branch:x.branches[0]?.id||null);
      setSelectedBranchState(candidate||null);
      if(candidate&&typeof window!=="undefined")localStorage.setItem(storageKey,String(candidate));
    }catch(e:any){setError(e.message||"خطا در دریافت تنظیمات");}
    finally{setLoading(false)}
  };
  useEffect(()=>{refresh()},[]);
  const setSelectedBranchId=(id:number)=>{setSelectedBranchState(id);if(typeof window!=="undefined")localStorage.setItem(storageKey,String(id))};
  const selectedBranch=useMemo(()=>data?.branches.find(b=>b.id===selectedBranchId)||null,[data,selectedBranchId]);
  const value:Value={data,loading,error,selectedBranchId,selectedBranch,setSelectedBranchId,refresh,can:(code)=>!!data?.permissions?.[code]};
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useSettings(){const x=useContext(Ctx);if(!x)throw new Error("useSettings must be used inside SettingsProvider");return x}

