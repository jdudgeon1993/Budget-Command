
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_845fe21c12f6ffee09387cd1e8eef801 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.accounts_rows_rx_state_ ?? [],((a_rx_state_,index_42412ca9c68def2bde12f9a7cf4e4a64)=>(jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["background"] : "#14141c", ["border"] : "1px solid #252535", ["borderRadius"] : "8px", ["padding"] : "10px 14px", ["width"] : "100%", ["alignItems"] : "center" }),direction:"row",key:index_42412ca9c68def2bde12f9a7cf4e4a64,gap:"3"},jsx(RadixThemesBox,{css:({ ["width"] : "10px", ["height"] : "10px", ["borderRadius"] : "50%", ["background"] : a_rx_state_?.["color"], ["flexShrink"] : "0" })},),jsx(RadixThemesText,{as:"p",css:({ ["flex"] : "1", ["color"] : "#f0f0fa" })},a_rx_state_?.["name"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "9px", ["color"] : "#4e4e6a", ["letterSpacing"] : "0.08em" })},a_rx_state_?.["type_upper"]),jsx(RadixThemesText,{as:"p",css:({ ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : a_rx_state_?.["bal_color"], ["fontWeight"] : "700" })},a_rx_state_?.["balance_fmt"])))))
    )
});
