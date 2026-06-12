
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Select_select_3ffe3ebc969cc2a86de4b2ac03822a98 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_5a1db8242d48affb78fcba3f2d858579 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_sheet_bucket", ({ ["v"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx("select",{css:({ ["background"] : "rgba(255,255,255,0.08)", ["border"] : "1px solid rgba(255,255,255,0.08)", ["borderRadius"] : "8px", ["color"] : "#FFFFFF", ["fontSize"] : "13px", ["padding"] : "8px 10px", ["width"] : "100%" }),onChange:on_change_5a1db8242d48affb78fcba3f2d858579,value:reflex___state____state__cura___state____app_state.sheet_bucket_rx_state_},children)
    )
});
