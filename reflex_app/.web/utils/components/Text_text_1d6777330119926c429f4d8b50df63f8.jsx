
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Text as RadixThemesText} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Text_text_1d6777330119926c429f4d8b50df63f8 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_bf048ce6d5c9ac950c34f8876c4751cb = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_edit_tx_type", ({ ["value"] : "out" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesText,{as:"p",css:({ ["&"] : ((reflex___state____state__cura___state____app_state.edit_tx_type_rx_state_?.valueOf?.() === "out"?.valueOf?.()) ? ({ ["font_size"] : "11px", ["font_family"] : "'Share Tech Mono', monospace", ["letter_spacing"] : "0.06em", ["padding"] : "4px 12px", ["border_radius"] : "20px", ["color"] : "#f87171", ["background"] : "#f871711a", ["border"] : "1px solid #f8717155", ["cursor"] : "pointer" }) : ({ ["font_size"] : "11px", ["font_family"] : "'Share Tech Mono', monospace", ["letter_spacing"] : "0.06em", ["padding"] : "4px 12px", ["border_radius"] : "20px", ["color"] : "#6868a2", ["background"] : "transparent", ["border"] : "1px solid #252535", ["cursor"] : "pointer", ["_hover"] : ({ ["color"] : "#8282a2", ["border_color"] : "#3c3c56" }) })) }),onClick:on_click_bf048ce6d5c9ac950c34f8876c4751cb},children)
    )
});
