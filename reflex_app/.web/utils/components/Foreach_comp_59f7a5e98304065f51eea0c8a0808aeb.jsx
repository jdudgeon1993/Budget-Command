
import {Fragment,memo,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isNotNullOrUndefined,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {Flex as RadixThemesFlex,Text as RadixThemesText,TextField as RadixThemesTextField} from "@radix-ui/themes"
import DebounceInput from "react-debounce-input"
import {jsx} from "@emotion/react"






export const Foreach_comp_59f7a5e98304065f51eea0c8a0808aeb = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.wi_rules_rows_rx_state_ ?? [],((r_rx_state_,index_fb78a4dfe0541d7e32348d048d7dfe21)=>(jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["padding"] : "6px 0", ["borderBottom"] : "1px solid #25253533", ["alignItems"] : "center", ["gap"] : "8px", ["width"] : "100%" }),direction:"row",key:index_fb78a4dfe0541d7e32348d048d7dfe21,gap:"3"},jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["gap"] : "2px", ["alignItems"] : "flex_start", ["flex"] : "1" }),direction:"column",gap:"3"},jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "13px", ["color"] : "#f0f0fa" })},r_rx_state_?.["name"]),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "11px", ["color"] : "#6868a2", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["letterSpacing"] : "0.08em" })},r_rx_state_?.["rule_type"])),jsx(RadixThemesText,{as:"p",css:({ ["fontSize"] : "11px", ["color"] : "#6868a2", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["minWidth"] : "60px", ["textAlign"] : "right" })},r_rx_state_?.["base_str"]),jsx(DebounceInput,{css:({ ["background"] : "#1c1c25", ["border"] : "1px solid #252535", ["borderRadius"] : "6px", ["padding"] : "4px 8px", ["color"] : "#f0f0fa", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["fontSize"] : "12px", ["width"] : "80px", ["textAlign"] : "right", ["&:focus"] : ({ ["borderColor"] : "#818cf8", ["outline"] : "none" }) }),debounceTimeout:300,element:RadixThemesTextField.Root,onChange:((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_wi_rule_override", ({ ["rule_id"] : r_rx_state_?.["id"], ["val"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))),placeholder:"new value",value:(isNotNullOrUndefined(r_rx_state_?.["override_val"]) ? r_rx_state_?.["override_val"] : "")},)))))
    )
});
