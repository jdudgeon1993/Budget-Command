
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isNotNullOrUndefined,isTrue} from "$/utils/state"
import DebounceInput from "react-debounce-input"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {TextField as RadixThemesTextField} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Debounceinput_debounceinput_7aa6b36eef31d454cf4d5164c10e0982 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_19befee94d174b4ddf60ce8ce9277f27 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_edit_pc_label", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(DebounceInput,{css:({ ["background"] : "rgba(255,255,255,0.08)", ["border"] : "1px solid rgba(255,255,255,0.08)", ["borderRadius"] : "8px", ["color"] : "#FFFFFF", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["fontSize"] : "12px", ["padding"] : "8px 12px", ["outline"] : "none", ["&:focus"] : ({ ["borderColor"] : "#BF5AF2" }), ["&:placeholder"] : ({ ["color"] : "#606088" }), ["flex"] : "2" }),debounceTimeout:300,element:RadixThemesTextField.Root,onChange:on_change_19befee94d174b4ddf60ce8ce9277f27,placeholder:"Label",type:"text",value:(isNotNullOrUndefined(reflex___state____state__cura___state____app_state.edit_pc_label_rx_state_) ? reflex___state____state__cura___state____app_state.edit_pc_label_rx_state_ : "")},)
    )
});
