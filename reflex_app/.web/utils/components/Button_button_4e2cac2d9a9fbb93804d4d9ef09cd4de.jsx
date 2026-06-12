
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Button_button_4e2cac2d9a9fbb93804d4d9ef09cd4de = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx("button",{css:({ ["width"] : "100%", ["padding"] : "13px", ["background"] : (reflex___state____state__cura___state____app_state.is_loading_rx_state_ ? "rgba(255,255,255,0.08)" : "#BF5AF2"), ["color"] : "#fff", ["border"] : "none", ["borderRadius"] : "8px", ["fontFamily"] : "'Inter', system-ui, sans-serif", ["--default-font-family"] : "'Inter', system-ui, sans-serif", ["fontSize"] : "13px", ["fontWeight"] : "600", ["letterSpacing"] : "0.08em", ["cursor"] : "pointer", ["textAlign"] : "center", ["marginTop"] : "4px", ["boxShadow"] : "0 4px 18px rgba(191,90,242,0.38)", ["&:hover"] : ({ ["opacity"] : "0.9", ["boxShadow"] : "0 6px 24px rgba(191,90,242,0.38)" }), ["&:active"] : ({ ["transform"] : "scale(0.98)" }) }),disabled:reflex___state____state__cura___state____app_state.is_loading_rx_state_,type:"submit"},children)
    )
});
