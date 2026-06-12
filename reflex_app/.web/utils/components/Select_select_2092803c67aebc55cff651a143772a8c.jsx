
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Select_select_2092803c67aebc55cff651a143772a8c = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_984b8488e4825372f70958251b285744 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_add_bkt_type", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx("select",{css:({ ["background"] : "rgba(255,255,255,0.08)", ["border"] : "1px solid rgba(255,255,255,0.08)", ["borderRadius"] : "8px", ["color"] : "#FFFFFF", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["fontSize"] : "13px", ["padding"] : "8px 10px", ["outline"] : "none", ["&:focus"] : ({ ["borderColor"] : "#BF5AF2" }), ["&:placeholder"] : ({ ["color"] : "#606088" }), ["flex"] : "0 0 auto", ["minWidth"] : "100px", ["maxWidth"] : "120px" }),onChange:on_change_984b8488e4825372f70958251b285744,value:reflex___state____state__cura___state____app_state.add_bkt_type_rx_state_},children)
    )
});
