
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_0ac43bf64374293778f067f0fd6d9b08 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.tl_hitters_rx_state_ ?? [],((h_rx_state_,index_ce73459e11c19297d0443c8446d5c0ca)=>(jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "6px 0", ["alignItems"] : "center", ["gap"] : "10px", ["width"] : "100%" }),direction:"row",key:index_ce73459e11c19297d0443c8446d5c0ca,gap:"3"},jsx(Fragment,{},((h_rx_state_?.["paid"]?.valueOf?.() === "1"?.valueOf?.())?(jsx(Fragment,{},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#34d399", ["fontSize"] : "11px", ["flexShrink"] : "0", ["width"] : "16px" })},"\u2713"))):(jsx(Fragment,{},jsx(RadixThemesText,{as:"p",css:({ ["color"] : "#f87171", ["fontSize"] : "18px", ["flexShrink"] : "0", ["lineHeight"] : "1", ["width"] : "16px" })},"\u00b7"))))),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["color"] : "#f0f0fa", ["flex"] : "1" })},h_rx_state_?.["name"]),jsx(RadixThemesBox,{css:({ ["width"] : "80px", ["background"] : "#1c1c25", ["borderRadius"] : "2px", ["overflow"] : "hidden", ["flexShrink"] : "0" })},jsx(RadixThemesBox,{css:({ ["height"] : "4px", ["borderRadius"] : "2px", ["width"] : h_rx_state_?.["pct"], ["background"] : ((h_rx_state_?.["paid"]?.valueOf?.() === "1"?.valueOf?.()) ? "#34d399" : "#f87171"), ["maxWidth"] : "100%" })},)),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : ((h_rx_state_?.["paid"]?.valueOf?.() === "1"?.valueOf?.()) ? "#8282a2" : "#f87171"), ["minWidth"] : "60px", ["textAlign"] : "right" })},h_rx_state_?.["amount_fmt"])))))
    )
});
