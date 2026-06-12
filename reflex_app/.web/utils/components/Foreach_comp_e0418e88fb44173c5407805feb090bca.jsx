
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_e0418e88fb44173c5407805feb090bca = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.tl_rows_rx_state_ ?? [],((r_rx_state_,index_caed976b3409d51cc1dcee4b40a00836)=>(jsx(Fragment,{key:index_caed976b3409d51cc1dcee4b40a00836},(() => {
  switch (JSON.stringify(r_rx_state_?.["rt"])) {
    case JSON.stringify("day"):
      return jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "10px 0 4px", ["borderBottom"] : "1px solid rgba(255,255,255,0.08)", ["marginTop"] : "8px", ["alignItems"] : "center", ["width"] : "100%" }),direction:"row",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["fontWeight"] : "600", ["color"] : ((r_rx_state_?.["td"]?.valueOf?.() === "1"?.valueOf?.()) ? "#BF5AF2" : "#9090B8"), ["letterSpacing"] : "0.04em", ["flex"] : "1" })},r_rx_state_?.["lbl"]),jsx(Fragment,{},((r_rx_state_?.["td"]?.valueOf?.() === "1"?.valueOf?.())?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["fontSize"] : "11px", ["color"] : "#BF5AF2", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["background"] : "#BF5AF218", ["border"] : "1px solid #BF5AF244", ["borderRadius"] : "4px", ["padding"] : "2px 6px" })},"Today"))):(jsx(Fragment,{},jsx(RadixThemesBox,{},))))));
      break;
    case JSON.stringify("paycheck"):
      return jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "8px 0 6px", ["borderBottom"] : "1px solid rgba(255,255,255,0.08)33", ["alignItems"] : "flex_start", ["gap"] : "10px", ["width"] : "100%" }),direction:"row",gap:"3"},jsx(RadixThemesBox,{css:({ ["width"] : "10px", ["height"] : "10px", ["borderRadius"] : "50%", ["background"] : "#30D158", ["flexShrink"] : "0", ["marginTop"] : "2px" })},),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "1px", ["alignItems"] : "flex_start" }),direction:"column",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#FFFFFF", ["fontWeight"] : "500" })},r_rx_state_?.["lbl"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#606088", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace" })},"Paycheck")),jsx(RadixThemesFlex,{css:({ ["flex"] : 1, ["justifySelf"] : "stretch", ["alignSelf"] : "stretch" })},),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["color"] : "#30D158", ["fontWeight"] : "600" })},r_rx_state_?.["amt"]));
      break;
    case JSON.stringify("bill"):
      return jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "8px 0 6px", ["borderBottom"] : "1px solid rgba(255,255,255,0.08)33", ["opacity"] : ((r_rx_state_?.["pa"]?.valueOf?.() === "1"?.valueOf?.()) ? "0.6" : "1"), ["alignItems"] : "flex_start", ["gap"] : "10px", ["width"] : "100%" }),direction:"row",gap:"3"},jsx(RadixThemesBox,{css:({ ["width"] : "10px", ["height"] : "10px", ["borderRadius"] : "50%", ["flexShrink"] : "0", ["marginTop"] : "2px", ["background"] : ((r_rx_state_?.["pd"]?.valueOf?.() === "1"?.valueOf?.()) ? "#606088" : ((r_rx_state_?.["sch"]?.valueOf?.() === "1"?.valueOf?.()) ? "#FF9F0A" : ((r_rx_state_?.["pa"]?.valueOf?.() === "1"?.valueOf?.()) ? "#606088" : "#FF453A"))), ["opacity"] : ((r_rx_state_?.["pa"]?.valueOf?.() === "1"?.valueOf?.()) ? "0.5" : "1") })},),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "1px", ["alignItems"] : "flex_start" }),direction:"column",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : ((r_rx_state_?.["pd"]?.valueOf?.() === "1"?.valueOf?.()) ? "#606088" : "#FFFFFF"), ["fontWeight"] : "500", ["textDecoration"] : ((r_rx_state_?.["pd"]?.valueOf?.() === "1"?.valueOf?.()) ? "line-through" : "none") })},r_rx_state_?.["lbl"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "11px", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["color"] : ((r_rx_state_?.["sch"]?.valueOf?.() === "1"?.valueOf?.()) ? "#FF9F0A" : "#606088") })},((r_rx_state_?.["sch"]?.valueOf?.() === "1"?.valueOf?.()) ? "Scheduled" : ((r_rx_state_?.["pd"]?.valueOf?.() === "1"?.valueOf?.()) ? "Paid" : "Bill due")))),jsx(RadixThemesFlex,{css:({ ["flex"] : 1, ["justifySelf"] : "stretch", ["alignSelf"] : "stretch" })},),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["fontWeight"] : "600", ["color"] : ((r_rx_state_?.["pd"]?.valueOf?.() === "1"?.valueOf?.()) ? "#606088" : ((r_rx_state_?.["sch"]?.valueOf?.() === "1"?.valueOf?.()) ? "#FF9F0A" : ((r_rx_state_?.["pa"]?.valueOf?.() === "1"?.valueOf?.()) ? "#606088" : "#FF453A"))), ["textDecoration"] : ((r_rx_state_?.["pd"]?.valueOf?.() === "1"?.valueOf?.()) ? "line-through" : "none") })},r_rx_state_?.["amt"]));
      break;
    default:
      return jsx(RadixThemesBox,{},);
      break;
  }
})()))))
    )
});
