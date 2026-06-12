
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_d68220d809377d8d99aeb517f8e47c9d = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.ledger_bucket_spend_rx_state_ ?? [],((row_rx_state_,index_4f95566bf3ed0d48c75e2970155db65e)=>(jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["marginBottom"] : "10px", ["gap"] : "5px", ["width"] : "100%" }),direction:"column",key:index_4f95566bf3ed0d48c75e2970155db65e,gap:"3"},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["alignItems"] : "center", ["gap"] : "8px", ["width"] : "100%" }),direction:"row",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["color"] : "#f0f0fa", ["flex"] : "1", ["minWidth"] : "0", ["overflow"] : "hidden", ["textOverflow"] : "ellipsis", ["whiteSpace"] : "nowrap", ["fontWeight"] : "600" })},row_rx_state_?.["name"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["color"] : ((row_rx_state_?.["is_over"]?.valueOf?.() === "1"?.valueOf?.()) ? "#f87171" : "#8282a2"), ["whiteSpace"] : "nowrap", ["flexShrink"] : "0" })},row_rx_state_?.["spent_fmt"])),jsx(RadixThemesBox,{css:({ ["height"] : "4px", ["borderRadius"] : "3px", ["background"] : "#1c1c25", ["overflow"] : "hidden", ["width"] : "100%" })},jsx(RadixThemesBox,{css:({ ["height"] : "100%", ["borderRadius"] : "3px", ["background"] : ((row_rx_state_?.["is_over"]?.valueOf?.() === "1"?.valueOf?.()) ? "#f87171" : "#818cf8"), ["width"] : row_rx_state_?.["pct_str"], ["transition"] : "width 0.35s ease" })},))))))
    )
});
