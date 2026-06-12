
import {Fragment,memo,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_c47a8984ec7ceaf936f53d6ae7ab93bb = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.payday_rows_rx_state_ ?? [],((row_rx_state_,index_0980a4860b3a0d5c1d183f4e74b34b39)=>(jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "10px 0", ["borderBottom"] : "1px solid #252535", ["opacity"] : ((row_rx_state_?.["included"]?.valueOf?.() === "1"?.valueOf?.()) ? "1" : "0.6"), ["alignItems"] : "center", ["width"] : "100%", ["gap"] : "10px" }),direction:"row",key:index_0980a4860b3a0d5c1d183f4e74b34b39,gap:"3"},jsx(RadixThemesBox,{css:({ ["width"] : "18px", ["height"] : "18px", ["borderRadius"] : "4px", ["border"] : ((row_rx_state_?.["included"]?.valueOf?.() === "1"?.valueOf?.()) ? "2px solid #818cf8" : "2px solid #3c3c56"), ["background"] : ((row_rx_state_?.["included"]?.valueOf?.() === "1"?.valueOf?.()) ? "#818cf8" : "transparent"), ["cursor"] : "pointer", ["flexShrink"] : "0", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" }),onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.toggle_payday_row", ({ ["rule_id"] : row_rx_state_?.["id"] }), ({  })))], [_e], ({  }))))},jsx(Fragment,{},((row_rx_state_?.["included"]?.valueOf?.() === "1"?.valueOf?.())?(jsx(Fragment,{},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "11px", ["color"] : "#fff", ["lineHeight"] : "1" })},"\u2713"))):(jsx(Fragment,{},jsx(RadixThemesBox,{},)))))),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "1px", ["alignItems"] : "flex-start", ["flex"] : "1" }),direction:"column",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["color"] : ((row_rx_state_?.["included"]?.valueOf?.() === "1"?.valueOf?.()) ? "#f0f0fa" : "#6868a2"), ["fontWeight"] : "600", ["lineHeight"] : "1.2" })},row_rx_state_?.["name"]),jsx(Fragment,{},((row_rx_state_?.["rule_type"]?.valueOf?.() === "internal"?.valueOf?.())?(jsx(Fragment,{},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#6868a2", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace" })},"\u2192 ",row_rx_state_?.["bucket_name"]))):(jsx(Fragment,{},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#fbbf24", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace" })},"External transfer")))))),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#6868a2", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["whiteSpace"] : "nowrap" })},row_rx_state_?.["value_str"]),jsx(RadixThemesText,{as:"p",css:({ ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["fontSize"] : "14px", ["fontWeight"] : "700", ["color"] : ((row_rx_state_?.["rule_type"]?.valueOf?.() === "internal"?.valueOf?.()) ? "#818cf8" : "#fbbf24"), ["whiteSpace"] : "nowrap", ["opacity"] : ((row_rx_state_?.["included"]?.valueOf?.() === "1"?.valueOf?.()) ? "1" : "0.4") })},row_rx_state_?.["amount_fmt"])))))
    )
});
