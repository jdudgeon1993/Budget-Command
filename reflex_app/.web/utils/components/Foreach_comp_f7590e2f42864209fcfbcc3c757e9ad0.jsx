
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_f7590e2f42864209fcfbcc3c757e9ad0 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.bva_month_hdrs_rx_state_ ?? [],((h_rx_state_,index_a69009915272fbc6e1862ed4b0017ea1)=>(jsx(Fragment,{key:index_a69009915272fbc6e1862ed4b0017ea1},(!((h_rx_state_?.["label"]?.valueOf?.() === ""?.valueOf?.()))?(jsx(Fragment,{},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "11px", ["color"] : "#6868a2", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["letterSpacing"] : "0.08em", ["minWidth"] : "130px", ["flex"] : "1", ["padding"] : "0 8px" })},h_rx_state_?.["label"]))):(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["minWidth"] : "130px", ["flex"] : "1" })},))))))))
    )
});
