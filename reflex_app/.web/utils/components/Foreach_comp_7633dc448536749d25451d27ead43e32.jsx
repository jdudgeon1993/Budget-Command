
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_7633dc448536749d25451d27ead43e32 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.cat_rollup_rows_rx_state_ ?? [],((row_rx_state_,index_6578433386de2dceadda476fab2e5e42)=>(jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["marginBottom"] : "12px", ["gap"] : "6px", ["width"] : "100%" }),direction:"column",key:index_6578433386de2dceadda476fab2e5e42,gap:"3"},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["alignItems"] : "center", ["width"] : "100%" }),direction:"row",gap:"3"},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "7px", ["alignItems"] : "center" }),direction:"row",gap:"3"},jsx(RadixThemesBox,{css:({ ["width"] : "9px", ["height"] : "9px", ["borderRadius"] : "50%", ["background"] : row_rx_state_?.["color"], ["flexShrink"] : "0" })},),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["color"] : "#f0f0fa", ["fontWeight"] : "600" })},row_rx_state_?.["name"])),jsx(RadixThemesFlex,{css:({ ["flex"] : 1, ["justifySelf"] : "stretch", ["alignSelf"] : "stretch" })},),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "8px", ["alignItems"] : "center" }),direction:"row",gap:"3"},jsx(Fragment,{},(!((row_rx_state_?.["budget_fmt"]?.valueOf?.() === ""?.valueOf?.()))?(jsx(Fragment,{},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : "#6868a2" })},row_rx_state_?.["alloc_fmt"]," / ",row_rx_state_?.["budget_fmt"]))):(jsx(Fragment,{},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : "#6868a2" })},row_rx_state_?.["alloc_fmt"]))))),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["fontWeight"] : "700", ["color"] : ((row_rx_state_?.["is_funded"]?.valueOf?.() === "1"?.valueOf?.()) ? "#34d399" : "#fbbf24") })},row_rx_state_?.["pct_str"]))),jsx(RadixThemesBox,{css:({ ["height"] : "5px", ["borderRadius"] : "3px", ["background"] : "#1c1c25", ["overflow"] : "hidden", ["width"] : "100%" })},jsx(RadixThemesBox,{css:({ ["height"] : "100%", ["borderRadius"] : "3px", ["background"] : ((row_rx_state_?.["is_funded"]?.valueOf?.() === "1"?.valueOf?.()) ? "#34d399" : "#818cf8"), ["width"] : row_rx_state_?.["pct_str"], ["transition"] : "width 0.35s ease" })},))))))
    )
});
