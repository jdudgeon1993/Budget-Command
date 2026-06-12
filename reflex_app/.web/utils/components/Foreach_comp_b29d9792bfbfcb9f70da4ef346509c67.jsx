
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_b29d9792bfbfcb9f70da4ef346509c67 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.wi_rows_rx_state_ ?? [],((r_rx_state_,index_7281961c38800c9f2ca4231dce6aaf9c)=>(jsx(Fragment,{key:index_7281961c38800c9f2ca4231dce6aaf9c},(() => {
  switch (JSON.stringify(r_rx_state_?.["rt"])) {
    case JSON.stringify("ph"):
      return jsx(RadixThemesBox,{css:({ ["background"] : ((r_rx_state_?.["pt"]?.valueOf?.() === "gap"?.valueOf?.()) ? "#1c1c25" : "#14141c"), ["border"] : ((r_rx_state_?.["shf"]?.valueOf?.() === "1"?.valueOf?.()) ? "2px solid #f87171" : ((r_rx_state_?.["pt"]?.valueOf?.() === "gap"?.valueOf?.()) ? "1px solid #252535" : "1px solid #3c3c56")), ["borderRadius"] : "10px 10px 0 0", ["padding"] : "12px 14px 8px", ["marginTop"] : "8px" })},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["alignItems"] : "center", ["width"] : "100%" }),direction:"row",gap:"3"},jsx(RadixThemesBox,{css:({ ["fontSize"] : "8px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["letterSpacing"] : "0.1em", ["padding"] : "2px 6px", ["borderRadius"] : "4px", ["background"] : ((r_rx_state_?.["pt"]?.valueOf?.() === "gap"?.valueOf?.()) ? "#1c1c25" : "#818cf822"), ["color"] : ((r_rx_state_?.["pt"]?.valueOf?.() === "gap"?.valueOf?.()) ? "#4e4e6a" : "#818cf8"), ["border"] : ((r_rx_state_?.["pt"]?.valueOf?.() === "gap"?.valueOf?.()) ? "1px solid #252535" : "1px solid #818cf844"), ["flexShrink"] : "0" })},((r_rx_state_?.["pt"]?.valueOf?.() === "gap"?.valueOf?.()) ? "GAP" : "PAY")),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "1px", ["alignItems"] : "flex-start", ["flex"] : "1" }),direction:"column",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["fontWeight"] : "600", ["color"] : "#f0f0fa" })},r_rx_state_?.["lbl"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "10px", ["color"] : "#4e4e6a" })},r_rx_state_?.["sub"])),jsx(RadixThemesFlex,{css:({ ["flex"] : 1, ["justifySelf"] : "stretch", ["alignSelf"] : "stretch" })},),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "0px", ["alignItems"] : "flex-end" }),direction:"column",gap:"3"},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "0px" }),direction:"row",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : r_rx_state_?.["c1"] })},r_rx_state_?.["sgn"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : r_rx_state_?.["c1"] })},r_rx_state_?.["amt"])),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "14px", ["fontWeight"] : "700", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : ((r_rx_state_?.["ebn"]?.valueOf?.() === "1"?.valueOf?.()) ? "#f87171" : "#f0f0fa") })},r_rx_state_?.["ebf"]))));
      break;
    case JSON.stringify("inc"):
      return jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["background"] : "#34d3990a", ["padding"] : "6px 14px", ["borderLeft"] : "2px solid #34d39933", ["borderRight"] : "1px solid #3c3c56", ["width"] : "100%", ["alignItems"] : "center" }),direction:"row",justify:"between",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["flexShrink"] : "0" })},"\ud83d\udcb0"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#f0f0fa", ["flex"] : "1" })},r_rx_state_?.["lbl"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : "#34d399" })},r_rx_state_?.["amt"]));
      break;
    case JSON.stringify("xfr"):
      return jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["background"] : "#fbbf240a", ["padding"] : "6px 14px", ["borderLeft"] : "2px solid #fbbf2433", ["borderRight"] : "1px solid #3c3c56", ["width"] : "100%", ["alignItems"] : "center" }),direction:"row",justify:"between",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#4e4e6a", ["flexShrink"] : "0" })},"\u2192"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#8282a2", ["flex"] : "1" })},r_rx_state_?.["lbl"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : "#fbbf24" })},r_rx_state_?.["amt"]));
      break;
    case JSON.stringify("sbh"):
      return jsx(RadixThemesBox,{css:({ ["padding"] : "6px 14px 2px", ["background"] : ((r_rx_state_?.["c1"]?.valueOf?.() === "#34d399"?.valueOf?.()) ? "#34d39908" : "#f8717108"), ["borderLeft"] : ((r_rx_state_?.["c1"]?.valueOf?.() === "#34d399"?.valueOf?.()) ? "2px solid #34d39944" : "2px solid #f8717144"), ["borderRight"] : "1px solid #3c3c56" })},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "9px", ["color"] : r_rx_state_?.["c1"], ["letterSpacing"] : "0.1em", ["textTransform"] : "uppercase", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace" })},r_rx_state_?.["lbl"]));
      break;
    case JSON.stringify("fdt"):
      return jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "9px", ["color"] : "#4e4e6a", ["letterSpacing"] : "0.08em", ["textTransform"] : "uppercase", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["padding"] : "4px 14px 0", ["background"] : "#34d39908", ["borderLeft"] : "2px solid #34d39933", ["borderRight"] : "1px solid #3c3c56" })},r_rx_state_?.["lbl"]);
      break;
    case JSON.stringify("fbl"):
      return jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "4px 14px", ["background"] : "#34d39908", ["borderLeft"] : "2px solid #34d39933", ["borderRight"] : "1px solid #3c3c56", ["width"] : "100%", ["alignItems"] : "center" }),direction:"row",justify:"between",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#34d399", ["fontSize"] : "11px", ["flexShrink"] : "0" })},"\u2713"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#f0f0fa", ["flex"] : "1" })},r_rx_state_?.["lbl"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : "#34d399" })},r_rx_state_?.["amt"]));
      break;
    case JSON.stringify("fba"):
      return jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "3px 14px 5px", ["background"] : "#34d39908", ["borderLeft"] : "2px solid #34d39933", ["borderRight"] : "1px solid #3c3c56", ["borderTop"] : "1px solid #34d39922", ["width"] : "100%" }),direction:"row",justify:"between",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "10px", ["color"] : "#4e4e6a", ["flex"] : "1" })},"Balance"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "11px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : "#8282a2" })},r_rx_state_?.["lbl"]));
      break;
    case JSON.stringify("udt"):
      return jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "9px", ["color"] : "#4e4e6a", ["letterSpacing"] : "0.08em", ["textTransform"] : "uppercase", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["padding"] : "4px 14px 0", ["background"] : "#f8717108", ["borderLeft"] : "2px solid #f8717133", ["borderRight"] : "1px solid #3c3c56" })},r_rx_state_?.["lbl"]);
      break;
    case JSON.stringify("ubl"):
      return jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "4px 14px", ["background"] : "#f8717108", ["borderLeft"] : "2px solid #f8717133", ["borderRight"] : "1px solid #3c3c56", ["width"] : "100%", ["alignItems"] : "center" }),direction:"row",justify:"between",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#fbbf24", ["fontSize"] : "11px", ["flexShrink"] : "0" })},"\u26a0"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#f0f0fa", ["flex"] : "1" })},r_rx_state_?.["lbl"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : "#f87171" })},r_rx_state_?.["amt"]));
      break;
    case JSON.stringify("uba"):
      return jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "3px 14px 5px", ["background"] : "#f8717108", ["borderLeft"] : "2px solid #f8717133", ["borderRight"] : "1px solid #3c3c56", ["borderTop"] : "1px solid #f8717122", ["width"] : "100%" }),direction:"row",justify:"between",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "10px", ["color"] : "#4e4e6a", ["flex"] : "1" })},"Balance"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "11px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : ((r_rx_state_?.["neg"]?.valueOf?.() === "1"?.valueOf?.()) ? "#f87171" : "#8282a2") })},r_rx_state_?.["lbl"]));
      break;
    case JSON.stringify("pf"):
      return jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["background"] : "#14141c", ["border"] : ((r_rx_state_?.["shf"]?.valueOf?.() === "1"?.valueOf?.()) ? "2px solid #f87171" : "1px solid #3c3c56"), ["borderTop"] : "1px solid #252535", ["borderRadius"] : "0 0 10px 10px", ["padding"] : "10px 14px 12px", ["marginBottom"] : "2px", ["width"] : "100%", ["gap"] : "4px" }),direction:"column",gap:"3"},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["width"] : "100%" }),direction:"row",justify:"between",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "10px", ["color"] : "#4e4e6a", ["flex"] : "1" })},"End Balance"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "14px", ["fontWeight"] : "700", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : ((r_rx_state_?.["ebn"]?.valueOf?.() === "1"?.valueOf?.()) ? "#f87171" : "#f0f0fa") })},r_rx_state_?.["ebf"])),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["width"] : "100%" }),direction:"row",justify:"between",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "10px", ["color"] : "#4e4e6a", ["flex"] : "1" })},"Safe to spend from here"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : r_rx_state_?.["c1"], ["fontWeight"] : "600" })},r_rx_state_?.["amt"])),jsx(Fragment,{},((r_rx_state_?.["shf"]?.valueOf?.() === "1"?.valueOf?.())?(jsx(Fragment,{},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "10px", ["color"] : "#f87171", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace" })},"\u26a0 Shortfall \u2014 balance goes negative"))):(jsx(Fragment,{},jsx(RadixThemesBox,{},))))));
      break;
    default:
      return jsx(RadixThemesBox,{},);
      break;
  }
})()))))
    )
});
