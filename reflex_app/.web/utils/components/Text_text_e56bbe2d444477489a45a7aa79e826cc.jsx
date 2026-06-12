
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Text as RadixThemesText} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Text_text_e56bbe2d444477489a45a7aa79e826cc = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_bf048ce6d5c9ac950c34f8876c4751cb = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_edit_tx_type", ({ ["value"] : "out" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesText,{as:"p",css:({ ["&"] : ((reflex___state____state__cura___state____app_state.edit_tx_type_rx_state_?.valueOf?.() === "out"?.valueOf?.()) ? ({ ["font_size"] : "11px", ["font_family"] : "'JetBrains Mono', monospace", ["letter_spacing"] : "0.06em", ["padding"] : "4px 12px", ["border_radius"] : "20px", ["color"] : "#FF453A", ["background"] : "#FF453A1a", ["border"] : "1px solid #FF453A55", ["cursor"] : "pointer" }) : ({ ["font_size"] : "11px", ["font_family"] : "'JetBrains Mono', monospace", ["letter_spacing"] : "0.06em", ["padding"] : "4px 12px", ["border_radius"] : "20px", ["color"] : "#606088", ["background"] : "transparent", ["border"] : "1px solid rgba(255,255,255,0.08)", ["cursor"] : "pointer", ["_hover"] : ({ ["color"] : "#9090B8", ["border_color"] : "rgba(255,255,255,0.14)" }) })) }),onClick:on_click_bf048ce6d5c9ac950c34f8876c4751cb},children)
    )
});
