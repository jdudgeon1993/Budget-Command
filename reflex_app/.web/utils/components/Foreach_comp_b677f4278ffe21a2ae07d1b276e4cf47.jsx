
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_b677f4278ffe21a2ae07d1b276e4cf47 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.trend_rows_rx_state_ ?? [],((row_rx_state_,index_bac9a67f82a647ade3c2bf0989043158)=>(jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "10px 12px", ["borderRadius"] : "8px", ["&:hover"] : ({ ["background"] : "rgba(255,255,255,0.08)" }), ["alignItems"] : "center", ["width"] : "100%", ["gap"] : "8px" }),direction:"row",key:index_bac9a67f82a647ade3c2bf0989043158,gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["color"] : "#FFFFFF", ["fontWeight"] : "600", ["minWidth"] : "100px", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace" })},row_rx_state_?.["label"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["color"] : "#30D158", ["minWidth"] : "100px" })},row_rx_state_?.["income_fmt"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["color"] : "#FF9F0A", ["minWidth"] : "100px" })},row_rx_state_?.["spent_fmt"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["color"] : row_rx_state_?.["net_color"], ["fontWeight"] : "600", ["minWidth"] : "100px" })},row_rx_state_?.["net_fmt"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["color"] : row_rx_state_?.["rate_color"] })},row_rx_state_?.["savings_rate"])))))
    )
});
