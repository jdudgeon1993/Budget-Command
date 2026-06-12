
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_092714b3118c54d3c76b4774e4ed88b9 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.accounts_rows_rx_state_ ?? [],((row_rx_state_,index_dc8f2c2f446406d45f60aa731385d62e)=>(jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["marginBottom"] : "7px", ["alignItems"] : "center", ["gap"] : "9px", ["width"] : "100%" }),direction:"row",key:index_dc8f2c2f446406d45f60aa731385d62e,gap:"3"},jsx(RadixThemesBox,{css:({ ["width"] : "9px", ["height"] : "9px", ["borderRadius"] : "50%", ["background"] : row_rx_state_?.["color"], ["flexShrink"] : "0" })},),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "14px", ["color"] : "#f0f0fa", ["flex"] : "1", ["minWidth"] : "0", ["overflow"] : "hidden", ["textOverflow"] : "ellipsis", ["whiteSpace"] : "nowrap" })},row_rx_state_?.["name"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "14px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["fontWeight"] : "700", ["color"] : row_rx_state_?.["bal_color"], ["whiteSpace"] : "nowrap", ["flexShrink"] : "0" })},row_rx_state_?.["balance_fmt"])))))
    )
});
