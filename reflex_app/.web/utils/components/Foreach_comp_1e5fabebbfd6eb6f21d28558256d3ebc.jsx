
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_1e5fabebbfd6eb6f21d28558256d3ebc = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.payee_spend_rows_rx_state_ ?? [],((row_rx_state_,index_569ff53fba4a65ecd85a134321c228cb)=>(jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "10px 14px", ["borderRadius"] : "8px", ["&:hover"] : ({ ["background"] : "rgba(255,255,255,0.08)" }), ["alignItems"] : "flex-start", ["width"] : "100%", ["gap"] : "12px" }),direction:"row",key:index_569ff53fba4a65ecd85a134321c228cb,gap:"3"},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "3px", ["alignItems"] : "stretch", ["flex"] : "1" }),direction:"column",gap:"3"},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "6px", ["alignItems"] : "center", ["flexWrap"] : "wrap" }),direction:"row",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["color"] : "#FFFFFF", ["fontWeight"] : "500" })},row_rx_state_?.["payee"]),jsx(Fragment,{},(!((row_rx_state_?.["cat_name"]?.valueOf?.() === ""?.valueOf?.()))?(jsx(Fragment,{},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "11px", ["color"] : "#606088", ["background"] : "rgba(255,255,255,0.08)", ["padding"] : "1px 6px", ["borderRadius"] : "4px", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace" })},row_rx_state_?.["cat_name"]))):(jsx(Fragment,{},jsx(RadixThemesBox,{},)))))),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "4px" }),direction:"row",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "11px", ["color"] : "#606088", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace" })},row_rx_state_?.["count"]," transactions"),jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#606088" })},"\u00b7"),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "11px", ["color"] : "#606088", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace" })},row_rx_state_?.["pct_str"]," of total")),jsx(RadixThemesBox,{css:({ ["height"] : "3px", ["borderRadius"] : "2px", ["background"] : "rgba(255,255,255,0.08)", ["width"] : "100%", ["overflow"] : "hidden" })},jsx(RadixThemesBox,{css:({ ["height"] : "3px", ["borderRadius"] : "2px", ["background"] : "#BF5AF2", ["width"] : row_rx_state_?.["bar_w"], ["transition"] : "width 0.3s ease" })},))),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "14px", ["fontWeight"] : "700", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["color"] : "#FF9F0A", ["whiteSpace"] : "nowrap" })},row_rx_state_?.["total_fmt"])))))
    )
});
