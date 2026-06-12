
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Select_select_b7e2e24c5b3034ab58414dc692277224 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_984b8488e4825372f70958251b285744 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_add_bkt_type", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx("select",{css:({ ["background"] : "#1c1c25", ["border"] : "1px solid #252535", ["borderRadius"] : "8px", ["color"] : "#f0f0fa", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["fontSize"] : "13px", ["padding"] : "8px 10px", ["outline"] : "none", ["&:focus"] : ({ ["borderColor"] : "#818cf8" }), ["&:placeholder"] : ({ ["color"] : "#6868a2" }), ["flex"] : "0 0 auto", ["minWidth"] : "100px", ["maxWidth"] : "120px" }),onChange:on_change_984b8488e4825372f70958251b285744,value:reflex___state____state__cura___state____app_state.add_bkt_type_rx_state_},children)
    )
});
