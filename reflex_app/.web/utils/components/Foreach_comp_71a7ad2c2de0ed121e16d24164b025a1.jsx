
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_71a7ad2c2de0ed121e16d24164b025a1 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.tl_rows_rx_state_ ?? [],((r_rx_state_,index_a76d6c59a655b1efc5154bafb181758d)=>(jsx(Fragment,{key:index_a76d6c59a655b1efc5154bafb181758d},(() => {
  switch (JSON.stringify(r_rx_state_?.["rt"])) {
    case JSON.stringify("wk"):
      return jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["background"] : "#1c1c25", ["border"] : "1px solid #252535", ["borderRadius"] : "8px", ["padding"] : "8px 12px", ["marginTop"] : "10px", ["alignItems"] : "center", ["width"] : "100%" }),direction:"row",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "11px", ["fontWeight"] : "600", ["color"] : "#8282a2", ["flex"] : "1", ["letterSpacing"] : "0.04em" })},r_rx_state_?.["lbl"]),jsx(Fragment,{},(!((r_rx_state_?.["wi"]?.valueOf?.() === ""?.valueOf?.()))?(jsx(Fragment,{},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "4px", ["alignItems"] : "center" }),direction:"row",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "11px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : "#34d399" })},r_rx_state_?.["wi"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "10px", ["color"] : "#4e4e6a" })},"in")))):(jsx(Fragment,{},jsx(RadixThemesBox,{},))))),jsx(Fragment,{},(!((r_rx_state_?.["wb"]?.valueOf?.() === ""?.valueOf?.()))?(jsx(Fragment,{},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "4px", ["alignItems"] : "center" }),direction:"row",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "11px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : "#fbbf24" })},r_rx_state_?.["wb"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "10px", ["color"] : "#4e4e6a" })},"bills")))):(jsx(Fragment,{},jsx(RadixThemesBox,{},))))));
      break;
    case JSON.stringify("dh"):
      return jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "6px 12px 2px", ["alignItems"] : "center", ["gap"] : "10px", ["width"] : "100%" }),direction:"row",gap:"3"},jsx(RadixThemesBox,{css:({ ["textAlign"] : "center", ["minWidth"] : "36px" })},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "18px", ["fontWeight"] : "700", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["lineHeight"] : "1", ["color"] : ((r_rx_state_?.["td"]?.valueOf?.() === "1"?.valueOf?.()) ? "#818cf8" : "#f0f0fa") })},r_rx_state_?.["dn"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "9px", ["color"] : "#4e4e6a", ["textTransform"] : "uppercase", ["letterSpacing"] : "0.08em", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace" })},r_rx_state_?.["wd"])),jsx(RadixThemesBox,{css:({ ["width"] : "1px", ["background"] : "#252535", ["height"] : "32px", ["flexShrink"] : "0" })},),jsx(RadixThemesBox,{css:({ ["flex"] : "1" })},),jsx(Fragment,{},((r_rx_state_?.["td"]?.valueOf?.() === "1"?.valueOf?.())?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["fontSize"] : "9px", ["color"] : "#818cf8", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["letterSpacing"] : "0.08em", ["background"] : "#818cf818", ["border"] : "1px solid #818cf844", ["borderRadius"] : "4px", ["padding"] : "2px 6px" })},"Today"))):(jsx(Fragment,{},jsx(RadixThemesBox,{},))))),jsx(Fragment,{},((r_rx_state_?.["pa"]?.valueOf?.() === "1"?.valueOf?.())?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["fontSize"] : "9px", ["color"] : "#4e4e6a", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["letterSpacing"] : "0.08em" })},"Past"))):(jsx(Fragment,{},jsx(RadixThemesBox,{},))))));
      break;
    case JSON.stringify("pc"):
      return jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "3px 12px", ["background"] : "#34d3990a", ["borderLeft"] : "3px solid #34d39944", ["alignItems"] : "center", ["gap"] : "8px", ["width"] : "100%" }),direction:"row",gap:"3"},jsx(RadixThemesBox,{css:({ ["width"] : "36px", ["flexShrink"] : "0" })},),jsx(RadixThemesBox,{css:({ ["width"] : "1px", ["background"] : "#252535", ["height"] : "100%", ["flexShrink"] : "0" })},),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "11px", ["flexShrink"] : "0" })},"\ud83d\udcb0"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#f0f0fa", ["flex"] : "1" })},r_rx_state_?.["lbl"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : "#34d399", ["fontWeight"] : "600" })},r_rx_state_?.["amt"]));
      break;
    case JSON.stringify("bl"):
      return jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "3px 12px", ["background"] : ((r_rx_state_?.["pd"]?.valueOf?.() === "1"?.valueOf?.()) ? "transparent" : "#f8717107"), ["borderLeft"] : ((r_rx_state_?.["pd"]?.valueOf?.() === "1"?.valueOf?.()) ? "3px solid #34d39933" : "3px solid #f8717155"), ["alignItems"] : "center", ["gap"] : "8px", ["width"] : "100%" }),direction:"row",gap:"3"},jsx(RadixThemesBox,{css:({ ["width"] : "36px", ["flexShrink"] : "0" })},),jsx(RadixThemesBox,{css:({ ["width"] : "1px", ["background"] : "#252535", ["height"] : "100%", ["flexShrink"] : "0" })},),jsx(Fragment,{},((r_rx_state_?.["pd"]?.valueOf?.() === "1"?.valueOf?.())?(jsx(Fragment,{},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#34d399", ["fontSize"] : "11px", ["flexShrink"] : "0" })},"\u2713"))):(jsx(Fragment,{},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#f87171", ["fontSize"] : "18px", ["flexShrink"] : "0", ["lineHeight"] : "1" })},"\u00b7"))))),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#f0f0fa", ["flex"] : "1" })},r_rx_state_?.["lbl"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : ((r_rx_state_?.["pd"]?.valueOf?.() === "1"?.valueOf?.()) ? "#4e4e6a" : "#f87171") })},r_rx_state_?.["amt"]));
      break;
    default:
      return jsx(RadixThemesBox,{},);
      break;
  }
})()))))
    )
});
