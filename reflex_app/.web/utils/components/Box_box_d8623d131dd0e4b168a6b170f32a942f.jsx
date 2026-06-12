
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_d8623d131dd0e4b168a6b170f32a942f = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_72efb9d6423c43f84e3079cb3f776f97 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.finish_reconcile", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["flex"] : "2", ["padding"] : "11px", ["borderRadius"] : "8px", ["background"] : (reflex___state____state__cura___state____app_state.recon_can_finish_rx_state_ ? (reflex___state____state__cura___state____app_state.recon_saving_rx_state_ ? "rgba(255,255,255,0.08)" : "#30D158") : "rgba(255,255,255,0.08)"), ["color"] : (reflex___state____state__cura___state____app_state.recon_can_finish_rx_state_ ? "#fff" : "#606088"), ["border"] : (reflex___state____state__cura___state____app_state.recon_can_finish_rx_state_ ? "1px solid #30D158" : "1px solid rgba(255,255,255,0.08)"), ["fontSize"] : "12px", ["textAlign"] : "center", ["cursor"] : (reflex___state____state__cura___state____app_state.recon_can_finish_rx_state_ ? "pointer" : "default"), ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["fontWeight"] : "700", ["letterSpacing"] : "0.06em", ["&:hover"] : ({ ["opacity"] : (reflex___state____state__cura___state____app_state.recon_can_finish_rx_state_ ? "0.9" : "1") }), ["transition"] : "all 0.2s ease" }),onClick:on_click_72efb9d6423c43f84e3079cb3f776f97},children)
    )
});
