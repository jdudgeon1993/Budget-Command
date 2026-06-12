
import {Fragment,memo,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Switch as RadixThemesSwitch,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_a912e694097fc33cdebabc6b1ca5c4e4 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.alloc_rule_rows_rx_state_ ?? [],((row_rx_state_,index_029334881744d97aaa6d6c0079c2c9be)=>(jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["background"] : "rgba(255,255,255,0.05)", ["border"] : "1px solid rgba(255,255,255,0.08)", ["borderRadius"] : "8px", ["padding"] : "10px 12px", ["marginBottom"] : "5px", ["opacity"] : ((row_rx_state_?.["active_str"]?.valueOf?.() === "1"?.valueOf?.()) ? "1" : "0.5"), ["alignItems"] : "center", ["width"] : "100%", ["gap"] : "8px" }),direction:"row",key:index_029334881744d97aaa6d6c0079c2c9be,gap:"3"},jsx(RadixThemesBox,{css:({ ["width"] : "8px", ["height"] : "8px", ["borderRadius"] : "50%", ["background"] : ((row_rx_state_?.["rule_type"]?.valueOf?.() === "internal"?.valueOf?.()) ? "#BF5AF2" : "#FF9F0A"), ["flexShrink"] : "0" })},),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "1px", ["alignItems"] : "flex-start", ["flex"] : "1" }),direction:"column",gap:"3"},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "6px", ["alignItems"] : "center" }),direction:"row",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["color"] : ((row_rx_state_?.["active_str"]?.valueOf?.() === "1"?.valueOf?.()) ? "#FFFFFF" : "#606088"), ["fontWeight"] : "600" })},row_rx_state_?.["name"]),jsx(Fragment,{},((row_rx_state_?.["rule_type"]?.valueOf?.() === "internal"?.valueOf?.())?(jsx(Fragment,{},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "11px", ["color"] : "#BF5AF2", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["letterSpacing"] : "0.1em", ["background"] : "#BF5AF21a", ["padding"] : "1px 5px", ["borderRadius"] : "4px" })},"INTERNAL"))):(jsx(Fragment,{},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "11px", ["color"] : "#FF9F0A", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["letterSpacing"] : "0.1em", ["background"] : "#FF9F0A1a", ["padding"] : "1px 5px", ["borderRadius"] : "4px" })},"EXTERNAL")))))),jsx(Fragment,{},((row_rx_state_?.["rule_type"]?.valueOf?.() === "internal"?.valueOf?.())?(jsx(Fragment,{},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#606088", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace" })},row_rx_state_?.["value_str"]," \u2192 ",row_rx_state_?.["bucket_name"]))):(jsx(Fragment,{},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#606088", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace" })},row_rx_state_?.["value_str"]," (external transfer)")))))),jsx(RadixThemesFlex,{css:({ ["flex"] : 1, ["justifySelf"] : "stretch", ["alignSelf"] : "stretch" })},),jsx(RadixThemesSwitch,{checked:(row_rx_state_?.["active_str"]?.valueOf?.() === "1"?.valueOf?.()),color:"indigo",onCheckedChange:((_ev_0) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.toggle_alloc_rule_item", ({ ["rule_id"] : row_rx_state_?.["id"] }), ({  })))], [_ev_0], ({  }))))},),jsx(RadixThemesBox,{css:({ ["fontSize"] : "14px", ["color"] : "#606088", ["cursor"] : "pointer", ["padding"] : "2px 6px", ["borderRadius"] : "4px", ["&:hover"] : ({ ["color"] : "#FF453A", ["background"] : "#FF453A11" }) }),onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.delete_alloc_rule_item", ({ ["rule_id"] : row_rx_state_?.["id"] }), ({  })))], [_e], ({  }))))},"\u2715")))))
    )
});
