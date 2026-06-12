
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_876d5ee0bc5cfc8c70bcf2442338bd88 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_3afd465f89ffb4133e30b4f20295ae5a = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_panel", ({ ["name"] : "setup" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["color"] : ((reflex___state____state__cura___state____app_state.active_panel_rx_state_?.valueOf?.() === "setup"?.valueOf?.()) ? "#818cf8" : "#4e4e6a"), ["cursor"] : "pointer", ["padding"] : "6px", ["borderRadius"] : "8px", ["&:hover"] : ({ ["color"] : "#8282a2" }), ["&:active"] : ({ ["opacity"] : "0.7" }) }),onClick:on_click_3afd465f89ffb4133e30b4f20295ae5a},children)
    )
});
