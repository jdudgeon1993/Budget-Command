
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Text as RadixThemesText} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Text_text_6896f4c2538120b7585a2fc371d4865c = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_d06ce585d8f97e71e6eb1b37e6b09fd4 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_edit_tx_type", ({ ["value"] : "xfr" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesText,{as:"p",css:({ ["&"] : ((reflex___state____state__cura___state____app_state.edit_tx_type_rx_state_?.valueOf?.() === "xfr"?.valueOf?.()) ? ({ ["font_size"] : "11px", ["font_family"] : "'Share Tech Mono', monospace", ["letter_spacing"] : "0.06em", ["padding"] : "4px 12px", ["border_radius"] : "20px", ["color"] : "#8282a2", ["background"] : "#8282a21a", ["border"] : "1px solid #8282a255", ["cursor"] : "pointer" }) : ({ ["font_size"] : "11px", ["font_family"] : "'Share Tech Mono', monospace", ["letter_spacing"] : "0.06em", ["padding"] : "4px 12px", ["border_radius"] : "20px", ["color"] : "#4e4e6a", ["background"] : "transparent", ["border"] : "1px solid #252535", ["cursor"] : "pointer", ["_hover"] : ({ ["color"] : "#8282a2", ["border_color"] : "#3c3c56" }) })) }),onClick:on_click_d06ce585d8f97e71e6eb1b37e6b09fd4},children)
    )
});
