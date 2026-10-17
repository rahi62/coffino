// A branch/filter response may only update UI while it owns the latest request.
export function createBranchReportGate(){
  let generation=0;
  return {
    start(){return ++generation;},
    isCurrent(id){return id===generation;},
    invalidate(){generation+=1;},
  };
}
