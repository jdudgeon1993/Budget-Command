
import {Fragment,memo,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_c2bfee0f0b6d867596af0cb627a3483c = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.attention_rows_rx_state_ ?? [],((row_rx_state_,index_ae99cebbf029552a6db067676277a550)=>(jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "9px 12px", ["borderRadius"] : "8px", ["background"] : ((row_rx_state_?.["is_over"]?.valueOf?.() === "1"?.valueOf?.()) ? "#FF453A0d" : "#FF9F0A0a"), ["border"] : ((row_rx_state_?.["is_over"]?.valueOf?.() === "1"?.valueOf?.()) ? "1px solid #FF453A33" : "1px solid #FF9F0A22"), ["marginBottom"] : "6px", ["alignItems"] : "center", ["gap"] : "10px", ["width"] : "100%" }),direction:"row",key:index_ae99cebbf029552a6db067676277a550,gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "14px", ["color"] : "#FFFFFF", ["flex"] : "1", ["minWidth"] : "0", ["overflow"] : "hidden", ["textOverflow"] : "ellipsis", ["whiteSpace"] : "nowrap", ["fontWeight"] : "600" })},row_rx_state_?.["name"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["whiteSpace"] : "nowrap", ["flexShrink"] : "0", ["color"] : ((row_rx_state_?.["is_over"]?.valueOf?.() === "1"?.valueOf?.()) ? "#FF453A" : "#FF9F0A") })},row_rx_state_?.["label"]),jsx(Fragment,{},(!((row_rx_state_?.["is_over"]?.valueOf?.() === "1"?.valueOf?.()))?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["fontSize"] : "12px", ["padding"] : "4px 12px", ["borderRadius"] : "6px", ["border"] : "1px solid #BF5AF255", ["color"] : "#BF5AF2", ["cursor"] : "pointer", ["flexShrink"] : "0", ["&:hover"] : ({ ["background"] : "#BF5AF211" }) }),onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.fill_bucket", ({ ["bucket_id"] : row_rx_state_?.["id"], ["budget"] : row_rx_state_?.["budget"] }), ({  })))], [_e], ({  }))))},"Fill"))):(jsx(Fragment,{},jsx(RadixThemesBox,{},)))))))))
    )
});
