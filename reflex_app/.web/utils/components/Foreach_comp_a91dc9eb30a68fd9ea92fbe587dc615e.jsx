
import {Fragment,memo,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {Box as RadixThemesBox,Flex as RadixThemesFlex,Text as RadixThemesText} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Foreach_comp_a91dc9eb30a68fd9ea92fbe587dc615e = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.wi_pop_rules_rx_state_ ?? [],((r_rx_state_,index_d72bb38707503f610bf5b1aedad85d0d)=>(jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "6px 8px", ["borderRadius"] : "6px", ["background"] : "rgba(255,255,255,0.08)", ["marginBottom"] : "4px", ["alignItems"] : "center", ["gap"] : "8px", ["width"] : "100%" }),direction:"row",key:index_d72bb38707503f610bf5b1aedad85d0d,gap:"3"},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "2px", ["alignItems"] : "flex_start", ["flex"] : "1" }),direction:"column",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#9090B8", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace" })},((r_rx_state_?.["from_label"]?.valueOf?.() === "Default"?.valueOf?.()) ? "Default" : ("From "+r_rx_state_?.["from_label"]))),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "6px", ["alignItems"] : "center" }),direction:"row",gap:"3"},jsx(Fragment,{},((r_rx_state_?.["enabled"]?.valueOf?.() === "1"?.valueOf?.())?(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["fontSize"] : "10px", ["color"] : "#30D158", ["background"] : "#30D15818", ["borderRadius"] : "4px", ["padding"] : "1px 5px", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace" })},"ON"))):(jsx(Fragment,{},jsx(RadixThemesBox,{css:({ ["fontSize"] : "10px", ["color"] : "#606088", ["background"] : "rgba(255,255,255,0.08)", ["borderRadius"] : "4px", ["padding"] : "1px 5px", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace" })},"OFF"))))),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "12px", ["color"] : "#606088", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace" })},r_rx_state_?.["amount_fmt"]))),jsx(RadixThemesBox,{css:({ ["fontSize"] : "16px", ["color"] : "#606088", ["cursor"] : "pointer", ["padding"] : "4px 8px", ["borderRadius"] : "4px", ["&:hover"] : ({ ["color"] : "#FF453A", ["background"] : "#FF453A12" }) }),onClick:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.del_wi_timeline_rule", ({ ["bid"] : reflex___state____state__cura___state____app_state.wi_pop_bkt_id_rx_state_, ["rule_idx"] : r_rx_state_?.["idx"] }), ({  })))], [_e], ({  })))),role:"button",tabIndex:0},"\u00d7")))))
    )
});
