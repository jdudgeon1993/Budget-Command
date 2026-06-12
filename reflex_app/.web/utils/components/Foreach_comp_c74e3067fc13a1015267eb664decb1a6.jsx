
import {Fragment,memo,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_c74e3067fc13a1015267eb664decb1a6 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.attention_rows_rx_state_ ?? [],((row_rx_state_,index_ae99cebbf029552a6db067676277a550)=>(jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "9px 12px", ["borderRadius"] : "8px", ["background"] : ((row_rx_state_?.["is_over"]?.valueOf?.() === "1"?.valueOf?.()) ? "#f871710d" : "#fbbf240a"), ["border"] : ((row_rx_state_?.["is_over"]?.valueOf?.() === "1"?.valueOf?.()) ? "1px solid #f8717133" : "1px solid #fbbf2422"), ["marginBottom"] : "6px", ["alignItems"] : "center", ["gap"] : "10px", ["width"] : "100%" }),direction:"row",key:index_ae99cebbf029552a6db067676277a550,gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "14px", ["color"] : "#f0f0fa", ["flex"] : "1", ["minWidth"] : "0", ["overflow"] : "hidden", ["textOverflow"] : "ellipsis", ["whiteSpace"] : "nowrap", ["fontWeight"] : "600" })},row_rx_state_?.["name"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["whiteSpace"] : "nowrap", ["flexShrink"] : "0", ["color"] : ((row_rx_state_?.["is_over"]?.valueOf?.() === "1"?.valueOf?.()) ? "#f87171" : "#fbbf24") })},row_rx_state_?.["label"]),jsx(Fragment,{},(!((row_rx_state_?.["is_over"]?.valueOf?.() === "1"?.valueOf?.()))?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["fontSize"] : "12px", ["padding"] : "4px 12px", ["borderRadius"] : "6px", ["border"] : "1px solid #818cf855", ["color"] : "#818cf8", ["cursor"] : "pointer", ["flexShrink"] : "0", ["&:hover"] : ({ ["background"] : "#818cf811" }) }),onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.fill_bucket", ({ ["bucket_id"] : row_rx_state_?.["id"], ["budget"] : row_rx_state_?.["budget"] }), ({  })))], [_e], ({  }))))},"Fill"))):(jsx(Fragment,{},jsx(RadixThemesBox,{},)))))))))
    )
});
