
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_497633009b6a8bf06d5da5563fb3892b = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.tl_rows_rx_state_ ?? [],((r_rx_state_,index_8741e9d92364a186156525c9f869d8bb)=>(jsx(Fragment,{key:index_8741e9d92364a186156525c9f869d8bb},(() => {
  switch (JSON.stringify(r_rx_state_?.["rt"])) {
    case JSON.stringify("day"):
      return jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "10px 0 4px", ["borderBottom"] : "1px solid #252535", ["marginTop"] : "8px", ["alignItems"] : "center", ["width"] : "100%" }),direction:"row",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["fontWeight"] : "600", ["color"] : ((r_rx_state_?.["td"]?.valueOf?.() === "1"?.valueOf?.()) ? "#818cf8" : "#8282a2"), ["letterSpacing"] : "0.04em", ["flex"] : "1" })},r_rx_state_?.["lbl"]),jsx(Fragment,{},((r_rx_state_?.["td"]?.valueOf?.() === "1"?.valueOf?.())?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["fontSize"] : "11px", ["color"] : "#818cf8", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["background"] : "#818cf818", ["border"] : "1px solid #818cf844", ["borderRadius"] : "4px", ["padding"] : "2px 6px" })},"Today"))):(jsx(Fragment,{},jsx(RadixThemesBox,{},))))));
      break;
    case JSON.stringify("paycheck"):
      return jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "8px 0 6px", ["borderBottom"] : "1px solid #25253533", ["alignItems"] : "flex_start", ["gap"] : "10px", ["width"] : "100%" }),direction:"row",gap:"3"},jsx(RadixThemesBox,{css:({ ["width"] : "10px", ["height"] : "10px", ["borderRadius"] : "50%", ["background"] : "#34d399", ["flexShrink"] : "0", ["marginTop"] : "2px" })},),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "1px", ["alignItems"] : "flex_start" }),direction:"column",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#f0f0fa", ["fontWeight"] : "500" })},r_rx_state_?.["lbl"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#6868a2", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace" })},"Paycheck")),jsx(RadixThemesFlex,{css:({ ["flex"] : 1, ["justifySelf"] : "stretch", ["alignSelf"] : "stretch" })},),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : "#34d399", ["fontWeight"] : "600" })},r_rx_state_?.["amt"]));
      break;
    case JSON.stringify("bill"):
      return jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "8px 0 6px", ["borderBottom"] : "1px solid #25253533", ["opacity"] : ((r_rx_state_?.["pa"]?.valueOf?.() === "1"?.valueOf?.()) ? "0.6" : "1"), ["alignItems"] : "flex_start", ["gap"] : "10px", ["width"] : "100%" }),direction:"row",gap:"3"},jsx(RadixThemesBox,{css:({ ["width"] : "10px", ["height"] : "10px", ["borderRadius"] : "50%", ["flexShrink"] : "0", ["marginTop"] : "2px", ["background"] : ((r_rx_state_?.["pd"]?.valueOf?.() === "1"?.valueOf?.()) ? "#6868a2" : ((r_rx_state_?.["sch"]?.valueOf?.() === "1"?.valueOf?.()) ? "#fbbf24" : ((r_rx_state_?.["pa"]?.valueOf?.() === "1"?.valueOf?.()) ? "#6868a2" : "#f87171"))), ["opacity"] : ((r_rx_state_?.["pa"]?.valueOf?.() === "1"?.valueOf?.()) ? "0.5" : "1") })},),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "1px", ["alignItems"] : "flex_start" }),direction:"column",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : ((r_rx_state_?.["pd"]?.valueOf?.() === "1"?.valueOf?.()) ? "#6868a2" : ((r_rx_state_?.["sch"]?.valueOf?.() === "1"?.valueOf?.()) ? "#f0f0fa" : "#f0f0fa")), ["fontWeight"] : "500", ["textDecoration"] : ((r_rx_state_?.["pd"]?.valueOf?.() === "1"?.valueOf?.()) ? "line-through" : "none") })},r_rx_state_?.["lbl"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "11px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : ((r_rx_state_?.["sch"]?.valueOf?.() === "1"?.valueOf?.()) ? "#fbbf24" : "#6868a2") })},((r_rx_state_?.["sch"]?.valueOf?.() === "1"?.valueOf?.()) ? "Scheduled" : ((r_rx_state_?.["pd"]?.valueOf?.() === "1"?.valueOf?.()) ? "Paid" : "Bill due")))),jsx(RadixThemesFlex,{css:({ ["flex"] : 1, ["justifySelf"] : "stretch", ["alignSelf"] : "stretch" })},),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["fontWeight"] : "600", ["color"] : ((r_rx_state_?.["pd"]?.valueOf?.() === "1"?.valueOf?.()) ? "#6868a2" : ((r_rx_state_?.["sch"]?.valueOf?.() === "1"?.valueOf?.()) ? "#fbbf24" : ((r_rx_state_?.["pa"]?.valueOf?.() === "1"?.valueOf?.()) ? "#6868a2" : "#f87171"))), ["textDecoration"] : ((r_rx_state_?.["pd"]?.valueOf?.() === "1"?.valueOf?.()) ? "line-through" : "none") })},r_rx_state_?.["amt"]));
      break;
    default:
      return jsx(RadixThemesBox,{},);
      break;
  }
})()))))
    )
});
