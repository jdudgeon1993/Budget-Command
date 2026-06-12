
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_8de828c6e64e993dfcb6216e7460a36c = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["background"] : "#14141c", ["border"] : (reflex___state____state__cura___state____app_state.rts_negative_rx_state_ ? "1px solid #f8717155" : (reflex___state____state__cura___state____app_state.rts_zero_rx_state_ ? "1px solid #34d39955" : "1px solid #252535")), ["borderRadius"] : "12px", ["padding"] : "18px 20px", ["marginBottom"] : "14px" })},children)
    )
});
