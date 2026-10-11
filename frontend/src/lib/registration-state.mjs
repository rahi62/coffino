export const REGISTRATION_STEPS=["mobile","verify","business","owner","branch"];

export function asciiDigits(value=""){
  return String(value).replace(/[۰-۹٠-٩]/g,ch=>{
    const fa="۰۱۲۳۴۵۶۷۸۹".indexOf(ch);
    if(fa>=0)return String(fa);
    const ar="٠١٢٣٤٥٦٧٨٩".indexOf(ch);
    return ar>=0?String(ar):ch;
  });
}

export function normalizeMobileInput(value=""){
  return asciiDigits(value).replace(/[\s\-()]/g,"").trim();
}

export function isStrongPassword(value=""){
  return String(value).length>=12&&/[A-Za-z]/.test(value)&&/\d/.test(value);
}

export function canContinueRegistration(step,state){
  switch(step){
    case "mobile": return /^((\+98|0098|98)?9|09)\d{9}$/.test(normalizeMobileInput(state.mobile||""));
    case "verify": return Boolean(state.verificationGrant);
    case "business": return Boolean(String(state.businessName||"").trim()&&state.businessType);
    case "owner": return Boolean(
      String(state.username||"").trim()&&
      isStrongPassword(state.password||"")&&
      state.password===state.passwordConfirmation
    );
    case "branch": return Boolean(String(state.branchName||"").trim());
    default:return false;
  }
}
